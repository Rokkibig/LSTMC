
import argparse
import pandas as pd
import lightgbm as lgb
import joblib
import os

def main():
    parser = argparse.ArgumentParser(description="Train a meta-model on the generated dataset.")
    parser.add_argument("--dataset", default="meta_dataset.csv", help="Path to the input dataset CSV file.")
    parser.add_argument("--outdir", default="models", help="Directory to save the trained meta-models.")
    args = parser.parse_args()

    print(f"Loading dataset from {args.dataset}...")
    df = pd.read_csv(args.dataset, index_col='date', parse_dates=True)

    # Identify feature and target columns
    feature_cols = [col for col in df.columns if not '_target' in col]
    target_cols = [col for col in df.columns if '_target' in col]

    if not target_cols:
        raise ValueError("No target columns found in the dataset. Make sure they end with '_target'.")

    print(f"Found {len(feature_cols)} features and {len(target_cols)} targets.")

    os.makedirs(args.outdir, exist_ok=True)

    # Train a separate model for each target currency
    for target_col in target_cols:
        currency = target_col.replace('_target', '')
        print(f"\n--- Training Meta-Model for: {currency} ---")

        # Create a clean dataset for this target, dropping rows where the target is NaN
        train_df = df[[*feature_cols, target_col]].dropna(subset=[target_col])
        
        if len(train_df) < 100: # Basic check for sufficient data
            print(f"Skipping {currency} due to insufficient data (less than 100 samples).")
            continue

        X = train_df[feature_cols]
        y = train_df[target_col]

        # Initialize and train the LightGBM model
        # These are basic parameters; they can be tuned later for better performance
        model = lgb.LGBMRegressor(
            random_state=42,
            n_estimators=150,       # More trees
            learning_rate=0.05,
            num_leaves=31
        )
        
        print(f"Training with {len(X)} samples...")
        model.fit(X, y)

        # Save the trained model
        model_path = os.path.join(args.outdir, f"meta_model_{currency}.joblib")
        joblib.dump(model, model_path)
        print(f"[OK] Saved trained model to {model_path}")

    print("\n[DONE] All meta-models have been trained and saved.")

if __name__ == "__main__":
    main()
