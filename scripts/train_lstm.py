import argparse
import json
import os
import random

import numpy as np
import tensorflow as tf
import yaml
from tensorflow.keras import layers, models


def load_cfg(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def to_categorical(y):
    mapping = {-1: 0, 0: 1, 1: 2}
    encoded = np.array([mapping[int(i)] for i in y], dtype=np.int32)
    return tf.keras.utils.to_categorical(encoded, num_classes=3)


def set_global_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)


def build_model(seq_len, feature_count):
    return models.Sequential([
        layers.Input(shape=(seq_len, feature_count)),
        layers.LSTM(64, return_sequences=True),
        layers.Dropout(0.2),
        layers.LSTM(32),
        layers.Dense(32, activation="relu"),
        layers.Dropout(0.2),
        layers.Dense(3, activation="softmax"),
    ])


def train_one(symbol, tf_name, tf_cfg):
    ds_path = f"data/{symbol}_{tf_name}_dataset.npz"
    meta_path = f"data/{symbol}_{tf_name}_meta.json"
    if not (os.path.exists(ds_path) and os.path.exists(meta_path)):
        print(f"[SKIP] no dataset/meta for {symbol} {tf_name}")
        return

    ds = np.load(ds_path, allow_pickle=True)
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    X_train, y_train = ds["X_train"], ds["y_train"]
    if len(X_train) == 0:
        print(f"[SKIP] not enough training data for {symbol} {tf_name}")
        return

    ytr = to_categorical(y_train)
    X_val, y_val = ds["X_val"], ds["y_val"]
    has_val = len(X_val) > 0
    if has_val:
        yva = to_categorical(y_val)
    else:
        yva = None
        print(f"[WARN] no validation split for {symbol} {tf_name}; training without validation data")

    model = build_model(meta["seq_len"], len(meta["features"]))
    model.compile(
        optimizer=tf.keras.optimizers.Adam(1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    callbacks = [
        tf.keras.callbacks.ReduceLROnPlateau(patience=5, factor=0.5, min_lr=1e-5),
        tf.keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
    ]

    fit_kwargs = {
        "epochs": 60,
        "batch_size": 256,
        "callbacks": callbacks,
        "verbose": 2,
    }
    if has_val:
        fit_kwargs["validation_data"] = (X_val, yva)

    model.fit(X_train, ytr, **fit_kwargs)
    os.makedirs("models", exist_ok=True)
    out_path = f"models/{symbol}_{tf_name}_lstm.h5"
    model.save(out_path)
    print("[OK] saved", out_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    cfg = load_cfg(args.config)

    seed = cfg.get("seed")
    if seed is not None:
        set_global_seed(int(seed))

    for symbol in cfg["symbols"]:
        for tf_name, tf_cfg in cfg["timeframes"].items():
            train_one(symbol, tf_name, tf_cfg)


if __name__ == "__main__":
    main()
