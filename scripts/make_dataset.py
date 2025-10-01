import argparse, json, os, sys, numpy as np, pandas as pd, yaml

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.utils import make_features, make_targets


def load_cfg(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def to_windows(df, features, target_col, seq_len):
    X, y = [], []
    a = df[features].values
    t = df[target_col].values
    for i in range(seq_len, len(df)):
        X.append(a[i-seq_len:i])
        y.append(t[i])
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int8)


def process_symbol(symbol, tf_name, tf_cfg, use_walk_forward=False):
    path = f"data/{symbol}_{tf_name}.csv"
    if not os.path.exists(path):
        print(f"[SKIP] no data: {path}")
        return
    df = pd.read_csv(path, parse_dates=["time"])
    df = make_features(df)
    df = make_targets(df, horizon=tf_cfg["horizon"], atr_mult=tf_cfg["atr_mult"])

    # Dynamically determine features from the dataframe columns, excluding the target and time
    features = [c for c in df.columns if c not in ["time", "y"]]

    X, y = to_windows(df, features, "y", tf_cfg["seq_len"])

    n = len(X)
    if n == 0:
        print(f"[SKIP] no windows for {symbol} {tf_name}")
        return
    if n < 1000:
        print(f"[WARN] too few windows ({n}) for {symbol} {tf_name}")

    if use_walk_forward:
        # Walk-forward validation з gap period для уникнення data leakage
        gap = int(n * 0.02)  # 2% gap між train і validation
        n_train = int(n * 0.7)
        n_val = int(n * 0.15)

        ds = {
            "X_train": X[:n_train], "y_train": y[:n_train],
            "X_val": X[n_train+gap:n_train+gap+n_val], "y_val": y[n_train+gap:n_train+gap+n_val],
            "X_test": X[n_train+gap+n_val:], "y_test": y[n_train+gap+n_val:]
        }
        print(f"[INFO] Using walk-forward validation with {gap} samples gap")
    else:
        # Стандартний split
        n_train = int(n*0.7); n_val = int(n*0.15)
        ds = {
            "X_train": X[:n_train], "y_train": y[:n_train],
            "X_val":   X[n_train:n_train+n_val], "y_val": y[n_train:n_train+n_val],
            "X_test":  X[n_train+n_val:], "y_test": y[n_train+n_val:]
        }

    os.makedirs("data", exist_ok=True)
    np.savez_compressed(f"data/{symbol}_{tf_name}_dataset.npz", **ds)
    meta = {"features":features,"seq_len":tf_cfg["seq_len"]}
    with open(f"data/{symbol}_{tf_name}_meta.json","w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    print(f"[OK] dataset {symbol} {tf_name} -> {n} windows (train:{len(ds['X_train'])}, val:{len(ds['X_val'])}, test:{len(ds['X_test'])})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--walk-forward", action="store_true",
                    help="Use walk-forward validation with gap period")
    args = ap.parse_args()
    cfg = load_cfg(args.config)

    for s in cfg["symbols"]:
        for tf_name, tf_cfg in cfg["timeframes"].items():
            process_symbol(s, tf_name, tf_cfg, use_walk_forward=args.walk_forward)


if __name__ == "__main__":
    main()
