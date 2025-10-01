import argparse
import json
import os
import random

import numpy as np
import tensorflow as tf
import yaml
from tensorflow.keras import layers, models, regularizers
from sklearn.utils.class_weight import compute_class_weight


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


def focal_loss(gamma=2.0, alpha=0.25):
    """Focal Loss для боротьби з class imbalance"""
    def focal_loss_fixed(y_true, y_pred):
        epsilon = tf.keras.backend.epsilon()
        y_pred = tf.clip_by_value(y_pred, epsilon, 1.0 - epsilon)
        cross_entropy = -y_true * tf.math.log(y_pred)
        weight = alpha * y_true * tf.pow((1 - y_pred), gamma)
        loss = weight * cross_entropy
        return tf.reduce_sum(loss, axis=1)
    return focal_loss_fixed


def build_lstm_model(seq_len, feature_count):
    """Покращена LSTM архітектура з BatchNorm та regularization"""
    return models.Sequential([
        layers.Input(shape=(seq_len, feature_count)),
        layers.LSTM(128, return_sequences=True, kernel_regularizer=regularizers.l2(0.001)),
        layers.BatchNormalization(),
        layers.Dropout(0.3),
        layers.LSTM(64, return_sequences=True, kernel_regularizer=regularizers.l2(0.001)),
        layers.BatchNormalization(),
        layers.Dropout(0.3),
        layers.LSTM(32, kernel_regularizer=regularizers.l2(0.001)),
        layers.Dense(64, activation="relu", kernel_regularizer=regularizers.l2(0.001)),
        layers.BatchNormalization(),
        layers.Dropout(0.3),
        layers.Dense(3, activation="softmax"),
    ])


def build_gru_model(seq_len, feature_count):
    """GRU альтернатива (швидша за LSTM)"""
    return models.Sequential([
        layers.Input(shape=(seq_len, feature_count)),
        layers.GRU(128, return_sequences=True, kernel_regularizer=regularizers.l2(0.001)),
        layers.BatchNormalization(),
        layers.Dropout(0.3),
        layers.GRU(64, return_sequences=True, kernel_regularizer=regularizers.l2(0.001)),
        layers.BatchNormalization(),
        layers.Dropout(0.3),
        layers.GRU(32, kernel_regularizer=regularizers.l2(0.001)),
        layers.Dense(64, activation="relu", kernel_regularizer=regularizers.l2(0.001)),
        layers.BatchNormalization(),
        layers.Dropout(0.3),
        layers.Dense(3, activation="softmax"),
    ])


def build_attention_lstm_model(seq_len, feature_count):
    """LSTM з attention mechanism"""
    inputs = layers.Input(shape=(seq_len, feature_count))

    # LSTM layers
    lstm_out = layers.LSTM(128, return_sequences=True, kernel_regularizer=regularizers.l2(0.001))(inputs)
    lstm_out = layers.BatchNormalization()(lstm_out)
    lstm_out = layers.Dropout(0.3)(lstm_out)

    lstm_out = layers.LSTM(64, return_sequences=True, kernel_regularizer=regularizers.l2(0.001))(lstm_out)
    lstm_out = layers.BatchNormalization()(lstm_out)
    lstm_out = layers.Dropout(0.3)(lstm_out)

    # Attention mechanism
    attention = layers.Dense(1, activation='tanh')(lstm_out)
    attention = layers.Flatten()(attention)
    attention = layers.Activation('softmax')(attention)
    attention = layers.RepeatVector(64)(attention)
    attention = layers.Permute([2, 1])(attention)

    # Apply attention
    sent_representation = layers.Multiply()([lstm_out, attention])
    sent_representation = layers.Lambda(lambda xin: tf.reduce_sum(xin, axis=1))(sent_representation)

    # Dense layers
    dense = layers.Dense(64, activation="relu", kernel_regularizer=regularizers.l2(0.001))(sent_representation)
    dense = layers.BatchNormalization()(dense)
    dense = layers.Dropout(0.3)(dense)
    outputs = layers.Dense(3, activation="softmax")(dense)

    return models.Model(inputs=inputs, outputs=outputs)


def build_model(seq_len, feature_count, model_type="lstm"):
    """Фабрика моделей"""
    if model_type == "gru":
        return build_gru_model(seq_len, feature_count)
    elif model_type == "attention":
        return build_attention_lstm_model(seq_len, feature_count)
    else:  # lstm
        return build_lstm_model(seq_len, feature_count)


def augment_data(X, y, num_augmented=2):
    """Data augmentation для часових рядів"""
    X_aug = []
    y_aug = []

    for i in range(len(X)):
        X_aug.append(X[i])
        y_aug.append(y[i])

        for _ in range(num_augmented):
            # Jittering - додавання невеликого шуму
            noise = np.random.normal(0, 0.01, X[i].shape)
            X_jittered = X[i] + noise
            X_aug.append(X_jittered)
            y_aug.append(y[i])

            # Magnitude warping
            scale = np.random.normal(1.0, 0.1, X[i].shape[1])
            X_warped = X[i] * scale
            X_aug.append(X_warped)
            y_aug.append(y[i])

    return np.array(X_aug, dtype=np.float32), np.array(y_aug)


def train_one(symbol, tf_name, tf_cfg, model_type="lstm", use_focal_loss=True, augment=True):
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

    # Data augmentation
    if augment and len(X_train) > 0:
        print(f"[INFO] Applying data augmentation...")
        X_train, y_train = augment_data(X_train, y_train, num_augmented=1)

    ytr = to_categorical(y_train)
    X_val, y_val = ds["X_val"], ds["y_val"]
    has_val = len(X_val) > 0
    if has_val:
        yva = to_categorical(y_val)
    else:
        yva = None
        print(f"[WARN] no validation split for {symbol} {tf_name}; training without validation data")

    # Compute class weights
    unique_classes = np.unique(y_train)
    class_weights_array = compute_class_weight('balanced', classes=unique_classes, y=y_train)
    mapping = {-1: 0, 0: 1, 1: 2}
    class_weights = {mapping[int(cls)]: weight for cls, weight in zip(unique_classes, class_weights_array)}
    print(f"[INFO] Class weights: {class_weights}")

    # Build model
    model = build_model(meta["seq_len"], len(meta["features"]), model_type=model_type)

    # Optimizer з weight decay (AdamW)
    optimizer = tf.keras.optimizers.Adam(
        learning_rate=1e-3,
        clipnorm=1.0  # Gradient clipping
    )

    # Loss function
    loss_fn = focal_loss(gamma=2.0, alpha=0.25) if use_focal_loss else "categorical_crossentropy"

    model.compile(
        optimizer=optimizer,
        loss=loss_fn,
        metrics=["accuracy", tf.keras.metrics.Precision(), tf.keras.metrics.Recall()],
    )

    # Callbacks
    callbacks = [
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss' if has_val else 'loss',
            patience=3,
            factor=0.5,
            min_lr=1e-6,
            verbose=1
        ),
        tf.keras.callbacks.EarlyStopping(
            monitor='val_loss' if has_val else 'loss',
            patience=10,
            restore_best_weights=True,
            verbose=1
        ),
    ]

    fit_kwargs = {
        "epochs": 100,  # Більше епох з early stopping
        "batch_size": 128,  # Менший batch для кращої генералізації
        "callbacks": callbacks,
        "verbose": 2,
        "class_weight": class_weights,
    }
    if has_val:
        fit_kwargs["validation_data"] = (X_val, yva)

    print(f"[INFO] Training {model_type} model for {symbol} {tf_name}...")
    history = model.fit(X_train, ytr, **fit_kwargs)

    # Зберігаємо модель
    os.makedirs("models", exist_ok=True)
    out_path = f"models/{symbol}_{tf_name}_{model_type}.h5"
    model.save(out_path)

    # Зберігаємо історію навчання
    history_path = f"models/{symbol}_{tf_name}_{model_type}_history.json"
    history_dict = {k: [float(v) for v in vals] for k, vals in history.history.items()}
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history_dict, f, indent=2)

    print(f"[OK] saved {out_path}")

    # Evaluation metrics
    if has_val:
        val_loss, val_acc, val_prec, val_rec = model.evaluate(X_val, yva, verbose=0)
        f1 = 2 * (val_prec * val_rec) / (val_prec + val_rec + 1e-9)
        print(f"[EVAL] Val Loss: {val_loss:.4f}, Acc: {val_acc:.4f}, Precision: {val_prec:.4f}, Recall: {val_rec:.4f}, F1: {f1:.4f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--model-type", default="lstm", choices=["lstm", "gru", "attention"],
                    help="Type of model architecture to train")
    ap.add_argument("--no-focal-loss", action="store_true",
                    help="Disable focal loss (use standard categorical crossentropy)")
    ap.add_argument("--no-augment", action="store_true",
                    help="Disable data augmentation")
    ap.add_argument("--ensemble", action="store_true",
                    help="Train all three model types for ensemble")
    args = ap.parse_args()
    cfg = load_cfg(args.config)

    seed = cfg.get("seed")
    if seed is not None:
        set_global_seed(int(seed))

    use_focal_loss = not args.no_focal_loss
    augment = not args.no_augment

    if args.ensemble:
        # Train all three architectures
        print("[INFO] Training ensemble of all model types...")
        for model_type in ["lstm", "gru", "attention"]:
            print(f"\n{'='*60}\n[INFO] Training {model_type.upper()} models\n{'='*60}")
            for symbol in cfg["symbols"]:
                for tf_name, tf_cfg in cfg["timeframes"].items():
                    train_one(symbol, tf_name, tf_cfg, model_type=model_type,
                             use_focal_loss=use_focal_loss, augment=augment)
    else:
        # Train single model type
        for symbol in cfg["symbols"]:
            for tf_name, tf_cfg in cfg["timeframes"].items():
                train_one(symbol, tf_name, tf_cfg, model_type=args.model_type,
                         use_focal_loss=use_focal_loss, augment=augment)


if __name__ == "__main__":
    main()
