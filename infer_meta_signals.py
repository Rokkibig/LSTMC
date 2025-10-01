import argparse
import json
import os
import pandas as pd
import joblib
import numpy as np
import yaml
from datetime import datetime

# --- Helper Functions ---

def load_cfg(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_trade_levels(entry_price: float, atr: float, side: str, symbol: str) -> dict:
    sl_distance = 1.5 * atr
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

def flatten_signals(signals: list) -> dict:
    """Flattens the list of signal objects into a single feature dictionary."""
    flat_row = {}
    for signal_item in signals:
        prefix = f"{signal_item['symbol']}_{signal_item['tf']}"
        signal_data = signal_item['signal']
        flat_row[f"{prefix}_p_short"] = signal_data['probabilities']['short']
        flat_row[f"{prefix}_p_no"] = signal_data['probabilities']['no']
        flat_row[f"{prefix}_p_long"] = signal_data['probabilities']['long']
        flat_row[f"{prefix}_trend_up"] = 1 if signal_data['trend_up'] else 0
    return flat_row

def main():
    parser = argparse.ArgumentParser(description="Generate a final meta-signal from all models.")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--signals-file", default="outputs/signals.json", help="Path to the generated signals file.")
    parser.add_argument("--models-dir", default="models", help="Directory with all trained models.")
    args = parser.parse_args()

    cfg = load_cfg(args.config)

    print(f"Loading primary signals from {args.signals_file}...")
    try:
        with open(args.signals_file, 'r', encoding='utf-8') as f:
            primary_signals_data = json.load(f)
            primary_signals = primary_signals_data['signals']
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Could not load or parse primary signals file: {e}. Exiting.")
        return
    
    if not primary_signals:
        print("No primary signals found in the input file. Exiting.")
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

    try:
        # Get feature order from first model
        first_model = next(iter(meta_models.values()))

        # Check if it's an ensemble or single model
        if isinstance(first_model, dict) and 'lgb_model' in first_model:
            # Ensemble model
            feature_order = first_model['lgb_model'].feature_names_in_
        else:
            # Single model
            feature_order = first_model.feature_names_in_

        features_df = features_df[feature_order]
    except Exception as e:
        print(f"[ERROR] Feature mismatch for meta-model: {e}")
        print("This likely means the meta-models are stale. Please run the full retraining pipeline.")
        return

    print("Predicting currency strength with meta-models...")
    predictions = {}
    for currency, model in meta_models.items():
        # Check if ensemble
        if isinstance(model, dict) and 'lgb_model' in model:
            lgb_pred = model['lgb_model'].predict(features_df)[0]
            xgb_pred = model['xgb_model'].predict(features_df)[0]
            prediction = model['lgb_weight'] * lgb_pred + model['xgb_weight'] * xgb_pred
        else:
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
        trade_levels = get_trade_levels(relevant_signal['price'], relevant_signal['atr'], side="LONG", symbol=recommended_pair)

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

if __name__ == "__main__":
    main()
