
import argparse
import json
import os
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import tensorflow as tf
import yaml
from tqdm import tqdm

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scripts.utils import make_features

# --- Helper Functions (adapted from infer_signals.py) ---

def load_cfg(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def build_trade(side: str, price: float, atr_value: float, params: dict, rounder: int, confidence: float):
    sl_mult = params["sl_mult"]
    tp1_mult = params["tp1_mult"]
    tp2_mult = params["tp2_mult"]
    if side == "LONG":
        entry = price
        sl = entry - sl_mult * atr_value
        tp1 = entry + tp1_mult * atr_value
        tp2 = entry + tp2_mult * atr_value
    else:
        entry = price
        sl = entry + sl_mult * atr_value
        tp1 = entry - tp1_mult * atr_value
        tp2 = entry - tp2_mult * atr_value
    return {
        "side": side,
        "entry": round(entry, rounder),
        "sl": round(sl, rounder),
        "tp1": round(tp1, rounder),
        "tp2": round(tp2, rounder),
        "confidence": confidence,
    }

def infer_one_historical(symbol, tf_name, prob_th, params, full_df, current_date):
    """
    Generates a signal for a given symbol/timeframe for a specific historical date.
    """
    meta_path = f"data/{symbol}_{tf_name}_meta.json"
    model_path = f"models/{symbol}_{tf_name}_lstm.h5"
    if not (os.path.exists(meta_path) and os.path.exists(model_path)):
        return None

    # Filter data up to the current historical date
    df = full_df[full_df['time'] <= current_date].copy()
    if df.empty:
        return None

    feat = make_features(df)
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    cols = meta["features"]
    seq_len = meta["seq_len"]
    
    if len(feat) < seq_len + 1:
        return None

    X = feat[cols].values[-seq_len:].astype(np.float32)[None, ...]
    model = tf.keras.models.load_model(model_path)
    proba = model.predict(X, verbose=0)[0]
    p_short, p_no, p_long = float(proba[0]), float(proba[1]), float(proba[2])

    last = feat.iloc[-1]
    price = float(last["Close"])
    atr_value = float(last["ATR14"])
    trend_up = int(last["TrendUp"]) == 1

    primary_side = "LONG" if p_long >= p_short else "SHORT"
    alt_side = "SHORT" if primary_side == "LONG" else "LONG"
    primary_conf = p_long if primary_side == "LONG" else p_short
    alt_conf = p_short if alt_side == "SHORT" else p_long

    rounder = 3 if symbol.endswith("JPY") else 5
    primary_trade = build_trade(primary_side, price, atr_value, params, rounder, primary_conf)
    alternative_trade = build_trade(alt_side, price, atr_value, params, rounder, alt_conf)

    prob_pass = primary_conf >= prob_th
    trend_pass = (primary_side == "LONG" and trend_up) or (primary_side == "SHORT" and not trend_up)
    status = "ACTIVE" if prob_pass and trend_pass else "WATCHLIST"
    issues = []
    if not prob_pass:
        issues.append("низька впевненість")
    if not trend_pass:
        issues.append("тренд проти сигналу")
    comment = "Фільтри пройдено, сигнал активний." if status == "ACTIVE" else "Очікуємо: " + ", ".join(issues)

    return {
        "symbol": symbol,
        "tf": tf_name,
        "time": current_date.isoformat() + "Z",
        "price": round(price, rounder),
        "atr": round(atr_value, rounder),
        "signal": {
            "decision": {
                "side": primary_side,
                "status": status,
                "confidence": primary_conf,
                "probability_pass": prob_pass,
                "trend_pass": trend_pass,
                "comment": comment,
            },
            "primary": primary_trade,
            "alternative": alternative_trade,
            "trend_up": trend_up,
            "probabilities": {"short": p_short, "no": p_no, "long": p_long},
        },
    }

def main():
    ap = argparse.ArgumentParser(description="Generate historical signals for backtesting.")
    ap.add_argument("--config", required=True, help="Path to config.yaml")
    ap.add_argument("--days", type=int, default=365, help="Number of past days to generate data for.")
    ap.add_argument("--outdir", default="outputs/history", help="Directory to save historical signal files.")
    args = ap.parse_args()

    cfg = load_cfg(args.config)
    prob_th = cfg["thresholds"]["prob"]
    
    # Pre-load all dataframes into memory to avoid repeated reads
    print("Pre-loading all historical data...")
    all_data = {}
    for symbol in cfg["symbols"]:
        for tf_name in cfg["timeframes"].keys():
            path = f"data/{symbol}_{tf_name}.csv"
            if os.path.exists(path):
                all_data[(symbol, tf_name)] = pd.read_csv(path, parse_dates=["time"])

    end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=args.days)
    
    date_range = [start_date + timedelta(days=x) for x in range(args.days)]

    print(f"Generating historical signals from {start_date.date()} to {end_date.date()}...")
    for current_date in tqdm(date_range, desc="Generating daily signals"):
        output = {
            "date": current_date.strftime("%Y-%m-%d"),
            "timezone": "UTC",
            "generated_at": datetime.now().isoformat() + "Z",
            "signals": [],
        }

        for symbol in cfg["symbols"]:
            for tf_name, tf_cfg in cfg["timeframes"].items():
                if (symbol, tf_name) in all_data:
                    full_df = all_data[(symbol, tf_name)]
                    result = infer_one_historical(symbol, tf_name, prob_th, tf_cfg, full_df, current_date)
                    if result:
                        output["signals"].append(result)
        
        # Save the output for the current day
        day_out_dir = os.path.join(args.outdir, current_date.strftime("%Y-%m-%d"))
        os.makedirs(day_out_dir, exist_ok=True)
        out_path = os.path.join(day_out_dir, "signals.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n[DONE] Historical data generation complete. Files saved in {args.outdir}")

if __name__ == "__main__":
    # This is a long-running script, suppress TensorFlow warnings for cleaner output
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' 
    tf.get_logger().setLevel('ERROR')
    main()
