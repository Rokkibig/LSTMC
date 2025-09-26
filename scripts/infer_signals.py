import argparse
import json
import os
from datetime import datetime

import numpy as np
import pandas as pd
import tensorflow as tf
import yaml

from utils import make_features


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


def infer_one(symbol, tf_name, prob_th, params):
    path = f"data/{symbol}_{tf_name}.csv"
    meta_path = f"data/{symbol}_{tf_name}_meta.json"
    model_path = f"models/{symbol}_{tf_name}_lstm.h5"
    if not (os.path.exists(path) and os.path.exists(meta_path) and os.path.exists(model_path)):
        print(f"[SKIP] infer missing {symbol} {tf_name}")
        return None

    df = pd.read_csv(path, parse_dates=["time"])
    feat = make_features(df)
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    cols = meta["features"]
    seq_len = meta["seq_len"]
    if len(feat) < seq_len + 1:
        print(f"[WARN] too short for infer {symbol} {tf_name}")
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
        "time": datetime.utcnow().isoformat() + "Z",
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
            "probabilities": {
                "short": p_short,
                "no": p_no,
                "long": p_long,
            },
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cfg = load_cfg(args.config)
    prob_th = cfg["thresholds"]["prob"]
    output = {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "timezone": "Europe/Berlin",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "disclaimer": "Сигнали згенеровані LSTM-моделлю. Це не фінансова порада. Торгуйте відповідально.",
        "signals": [],
    }

    for symbol in cfg["symbols"]:
        for tf_name, tf_cfg in cfg["timeframes"].items():
            result = infer_one(symbol, tf_name, prob_th, tf_cfg)
            if result:
                output["signals"].append(result)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("[OK] wrote", args.out)


if __name__ == "__main__":
    main()
