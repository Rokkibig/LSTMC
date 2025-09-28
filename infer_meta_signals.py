import argparse
import json
import os
import pandas as pd
import joblib
import numpy as np
import tensorflow as tf
import yaml
from datetime import datetime

from scripts.utils import make_features

# --- Helper Functions ---

def load_cfg(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_trade_levels(entry_price: float, atr: float, side: str, symbol: str) -> dict:
    """Calculates SL and TP levels based on a given price and ATR."""
    sl_distance = 1.5 * atr
    # Determine rounding based on the recommended pair, not the source pair
    rounder = 3 if "JPY" in symbol else 5

    if side == "LONG":
        sl = entry_price - sl_distance
        tp1 = entry_price + sl_distance
        tp2 = entry_price + 2 * sl_distance
    else:  # SHORT
        sl = entry_price + sl_distance
        tp1 = entry_price - sl_distance
        tp2 = entry_price - 2 * sl_distance

    return {
        "entry": round(entry_price, rounder),
        "sl": round(sl, rounder),
        "tp1": round(tp1, rounder),
        "tp2": round(tp2, rounder),
    }

def infer_one(symbol, tf_name, prob_th, params):
    """Generates primary signal data, including price and ATR for later use."""
    path = f"data/{symbol}_{tf_name}.csv"
    meta_path = f"data/{symbol}_{tf_name}_meta.json"
    model_path = f"models/{symbol}_{tf_name}_lstm.h5"
    if not (os.path.exists(path) and os.path.exists(meta_path) and os.path.exists(model_path)):
        return None

    df = pd.read_csv(path, parse_dates=["time"])
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

    return {
        "symbol": symbol, "tf": tf_name, "trend_up": trend_up,
        "price": price, "atr": atr_value,
        "probabilities": {"short": p_short, "no": p_no, "long": p_long}
    }

def flatten_signals(signals: list) -> dict:
    """Flattens the list of signal objects into a single feature dictionary."""
    flat_row = {}
    for signal_item in signals:
        prefix = f"{signal_item['symbol']}_{signal_item['tf']}"
        flat_row[f"{prefix}_p_short"] = signal_item['probabilities']['short']
        flat_row[f"{prefix}_p_no"] = signal_item['probabilities']['no']
        flat_row[f"{prefix}_p_long"] = signal_item['probabilities']['long']
        flat_row[f"{prefix}_trend_up"] = 1 if signal_item['trend_up'] else 0
    return flat_row

def main():
    parser = argparse.ArgumentParser(description="Generate a final meta-signal from all models.")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--models-dir", default="models", help="Directory with all trained models.")
    args = parser.parse_args()

    cfg = load_cfg(args.config)
    prob_th = cfg["thresholds"]["prob"]

    print("Generating primary signals from LSTM models...")
    primary_signals = []
    for symbol in cfg["symbols"]:
        for tf_name, tf_cfg in cfg["timeframes"].items():
            result = infer_one(symbol, tf_name, prob_th, tf_cfg)
            if result:
                primary_signals.append(result)
    
    if not primary_signals:
        print("Could not generate any primary signals. Exiting.")
        return

    features = flatten_signals(primary_signals)
    features_df = pd.DataFrame([features])

    print("Loading meta-models...")
    meta_models = {}
    for filename in os.listdir(args.models_dir):
        if filename.startswith("meta_model_") and filename.endswith(".joblib"):
            currency = filename.replace("meta_model_", "").replace(".joblib", "")
            model_path = os.path.join(args.models_dir, filename)
            meta_models[currency] = joblib.load(model_path)

    if not meta_models:
        print("No meta-models found. Did you run train_meta_model.py?")
        return

    any_model = next(iter(meta_models.values()))
    try:
        feature_order = any_model.feature_name_
        features_df = features_df[feature_order]
    except AttributeError:
        print("Warning: Could not get feature order from model. Assuming order is correct.")

    print("Predicting currency strength with meta-models...")
    predictions = {}
    for currency, model in meta_models.items():
        prediction = model.predict(features_df)[0]
        predictions[currency] = prediction

    if not predictions:
        print("No predictions were made.")
        return

    sorted_predictions = sorted(predictions.items(), key=lambda item: item[1], reverse=True)
    strongest = sorted_predictions[0]
    weakest = sorted_predictions[-1]
    recommended_pair = f"{strongest[0]}{weakest[0]}"

    trade_levels = None
    base_symbol_for_levels = f"{strongest[0]}USD"
    if strongest[0] == 'JPY': base_symbol_for_levels = "USDJPY"
    
    relevant_signal = next((s for s in primary_signals if s['symbol'] == base_symbol_for_levels and s['tf'] == 'H4'), None)
    
    if relevant_signal:
        print(f"Calculating trade levels based on {relevant_signal['symbol']} H4 data...")
        # Note: This is an approximation. For a true cross-pair like AUDEUR, the entry price
        # would be AUDUSD/EURUSD, and ATR would be more complex. Here we use the base pair's data.
        trade_levels = get_trade_levels(relevant_signal['price'], relevant_signal['atr'], side="LONG", symbol=recommended_pair)
    else:
        print(f"Warning: Could not find H4 data for {base_symbol_for_levels} to calculate trade levels.")

    output = {
        "generated_at": datetime.now().isoformat(),
        "strongest_currency": strongest[0],
        "strongest_prediction": strongest[1],
        "weakest_currency": weakest[0],
        "weakest_prediction": weakest[1],
        "recommended_pair": recommended_pair,
        "trade_levels": trade_levels
    }

    out_path = os.path.join("outputs", "meta_signal.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"[OK] Meta signal saved to {out_path}")

    print("\n----------------------------------------")
    print("--- Meta-Signal Summary ---")
    print("----------------------------------------")
    print(f"Найсильніша валюта: {strongest[0]} (Прогноз: {strongest[1]:+.4f}%)")
    print(f"Найслабша валюта:  {weakest[0]} (Прогноз: {weakest[1]:+.4f}%)")
    print("----------------------------------------")
    print(f"РЕКОМЕНДАЦІЯ: Розглянути LONG по {output['recommended_pair']}")
    if trade_levels:
        print("  Вхід:  ", trade_levels['entry'])
        print("  SL:    ", trade_levels['sl'])
        print("  TP1:   ", trade_levels['tp1'])
        print("  TP2:   ", trade_levels['tp2'])
    print("----------------------------------------\n")

if __name__ == "__main__":
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' 
    tf.get_logger().setLevel('ERROR')
    main()