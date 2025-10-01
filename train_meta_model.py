
import argparse
import pandas as pd
import lightgbm as lgb
import xgboost as xgb
import joblib
import os
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

def train_lgb_model(X_train, y_train, X_val=None, y_val=None):
    """Train LightGBM model з покращеними параметрами"""
    params = {
        'random_state': 42,
        'n_estimators': 500,
        'learning_rate': 0.03,
        'num_leaves': 31,
        'max_depth': 8,
        'min_child_samples': 20,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'reg_alpha': 0.1,
        'reg_lambda': 0.1,
        'verbose': -1,
    }

    if X_val is not None and y_val is not None:
        model = lgb.LGBMRegressor(**params)
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)]
        )
    else:
        model = lgb.LGBMRegressor(**params)
        model.fit(X_train, y_train)

    return model


def train_xgb_model(X_train, y_train, X_val=None, y_val=None):
    """Train XGBoost model для ensemble"""
    params = {
        'random_state': 42,
        'n_estimators': 500,
        'learning_rate': 0.03,
        'max_depth': 6,
        'min_child_weight': 3,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'reg_alpha': 0.1,
        'reg_lambda': 0.1,
        'verbosity': 0,
    }

    if X_val is not None and y_val is not None:
        model = xgb.XGBRegressor(**params)
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            early_stopping_rounds=50,
            verbose=False
        )
    else:
        model = xgb.XGBRegressor(**params)
        model.fit(X_train, y_train)

    return model


def create_ensemble_model(X_train, y_train, X_val, y_val):
    """Створює ensemble з LightGBM та XGBoost"""
    print("[INFO] Training LightGBM model...")
    lgb_model = train_lgb_model(X_train, y_train, X_val, y_val)

    print("[INFO] Training XGBoost model...")
    xgb_model = train_xgb_model(X_train, y_train, X_val, y_val)

    # Evaluate both models
    lgb_pred = lgb_model.predict(X_val)
    xgb_pred = xgb_model.predict(X_val)

    lgb_mse = mean_squared_error(y_val, lgb_pred)
    xgb_mse = mean_squared_error(y_val, xgb_pred)

    print(f"[INFO] LightGBM MSE: {lgb_mse:.6f}, XGBoost MSE: {xgb_mse:.6f}")

    # Weighted ensemble based on validation performance
    lgb_weight = (1 / lgb_mse) / ((1 / lgb_mse) + (1 / xgb_mse))
    xgb_weight = 1 - lgb_weight

    print(f"[INFO] Ensemble weights - LightGBM: {lgb_weight:.3f}, XGBoost: {xgb_weight:.3f}")

    return {
        'lgb_model': lgb_model,
        'xgb_model': xgb_model,
        'lgb_weight': lgb_weight,
        'xgb_weight': xgb_weight
    }


def main():
    parser = argparse.ArgumentParser(description="Train a meta-model on the generated dataset.")
    parser.add_argument("--dataset", default="meta_dataset.csv", help="Path to the input dataset CSV file.")
    parser.add_argument("--outdir", default="models", help="Directory to save the trained meta-models.")
    parser.add_argument("--ensemble", action="store_true", help="Train ensemble of LightGBM + XGBoost")
    parser.add_argument("--cv-folds", type=int, default=0, help="Number of time-series CV folds (0 to disable)")
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
        print(f"\n{'='*60}\n--- Training Meta-Model for: {currency} ---\n{'='*60}")

        # Create a clean dataset for this target, dropping rows where the target is NaN
        train_df = df[[*feature_cols, target_col]].dropna(subset=[target_col])

        if len(train_df) < 100:
            print(f"Skipping {currency} due to insufficient data (less than 100 samples).")
            continue

        X = train_df[feature_cols]
        y = train_df[target_col]

        # Time-series split for validation
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]

        print(f"Training samples: {len(X_train)}, Validation samples: {len(X_val)}")

        if args.ensemble:
            # Train ensemble model
            ensemble = create_ensemble_model(X_train, y_train, X_val, y_val)

            # Evaluate ensemble
            lgb_pred = ensemble['lgb_model'].predict(X_val)
            xgb_pred = ensemble['xgb_model'].predict(X_val)
            ensemble_pred = (ensemble['lgb_weight'] * lgb_pred + ensemble['xgb_weight'] * xgb_pred)

            mse = mean_squared_error(y_val, ensemble_pred)
            mae = mean_absolute_error(y_val, ensemble_pred)
            r2 = r2_score(y_val, ensemble_pred)

            print(f"[EVAL] Ensemble - MSE: {mse:.6f}, MAE: {mae:.6f}, R2: {r2:.4f}")

            # Save ensemble
            model_path = os.path.join(args.outdir, f"meta_model_{currency}.joblib")
            joblib.dump(ensemble, model_path)

        else:
            # Train single LightGBM model
            model = train_lgb_model(X_train, y_train, X_val, y_val)

            # Evaluate
            y_pred = model.predict(X_val)
            mse = mean_squared_error(y_val, y_pred)
            mae = mean_absolute_error(y_val, y_pred)
            r2 = r2_score(y_val, y_pred)

            print(f"[EVAL] MSE: {mse:.6f}, MAE: {mae:.6f}, R2: {r2:.4f}")

            # Feature importance
            feature_importance = pd.DataFrame({
                'feature': feature_cols,
                'importance': model.feature_importances_
            }).sort_values('importance', ascending=False)

            print(f"\n[INFO] Top 10 important features:")
            print(feature_importance.head(10).to_string(index=False))

            # Save model
            model_path = os.path.join(args.outdir, f"meta_model_{currency}.joblib")
            joblib.dump(model, model_path)

        print(f"[OK] Saved trained model to {model_path}")

        # Time-series cross-validation if requested
        if args.cv_folds > 0:
            print(f"\n[INFO] Running {args.cv_folds}-fold time-series cross-validation...")
            tscv = TimeSeriesSplit(n_splits=args.cv_folds)
            cv_scores = []

            for fold, (train_idx, val_idx) in enumerate(tscv.split(X), 1):
                X_cv_train, X_cv_val = X.iloc[train_idx], X.iloc[val_idx]
                y_cv_train, y_cv_val = y.iloc[train_idx], y.iloc[val_idx]

                cv_model = train_lgb_model(X_cv_train, y_cv_train)
                cv_pred = cv_model.predict(X_cv_val)
                cv_mse = mean_squared_error(y_cv_val, cv_pred)
                cv_scores.append(cv_mse)

                print(f"  Fold {fold}: MSE = {cv_mse:.6f}")

            print(f"[CV] Average MSE: {np.mean(cv_scores):.6f} ± {np.std(cv_scores):.6f}")

    print("\n[DONE] All meta-models have been trained and saved.")

if __name__ == "__main__":
    main()
