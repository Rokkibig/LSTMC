"""
Автоматичний запуск повного pipeline з усіма покращеннями
Включає: feature engineering, ensemble training, meta-models, evaluation
"""

import argparse
import glob
import os
import subprocess
import sys
from datetime import datetime


def run_cmd(args: list[str], description: str = ""):
    """Виконує команду та виводить результат"""
    print(f"\n{'='*80}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {description}")
    print(f"{'='*80}")
    print(f"Команда: {' '.join(args)}\n")

    try:
        result = subprocess.run(args, check=True, text=True, capture_output=False)
        print(f"\n✅ [OK] {description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ [ERROR] {description} failed with code {e.returncode}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Запуск повного покращеного pipeline для Forex LSTM"
    )

    # Pipeline options
    parser.add_argument(
        "--skip-fetch",
        action="store_true",
        help="Пропустити завантаження даних з MT5 (якщо дані вже є)"
    )
    parser.add_argument(
        "--skip-history",
        action="store_true",
        help="Пропустити генерацію історичних сигналів (довгий процес)"
    )
    parser.add_argument(
        "--model-type",
        default="ensemble",
        choices=["lstm", "gru", "attention", "ensemble"],
        help="Тип моделі для навчання (ensemble = всі три типи)"
    )
    parser.add_argument(
        "--meta-ensemble",
        action="store_true",
        help="Використовувати LightGBM + XGBoost ensemble для meta-моделі"
    )
    parser.add_argument(
        "--cv-folds",
        type=int,
        default=5,
        help="Кількість фолдів для time-series cross-validation (0 = вимкнути)"
    )
    parser.add_argument(
        "--no-augment",
        action="store_true",
        help="Вимкнути data augmentation"
    )
    parser.add_argument(
        "--no-focal-loss",
        action="store_true",
        help="Вимкнути focal loss (використовувати звичайний categorical crossentropy)"
    )
    parser.add_argument(
        "--history-days",
        type=int,
        default=365,
        help="Кількість днів для генерації історичних сигналів"
    )
    parser.add_argument(
        "--fast-mode",
        action="store_true",
        help="Швидкий режим: GRU, без augmentation, без history, без CV"
    )

    args = parser.parse_args()

    # Fast mode shortcuts
    if args.fast_mode:
        print("\n🚀 FAST MODE ENABLED")
        args.model_type = "gru"
        args.no_augment = True
        args.skip_history = True
        args.cv_folds = 0
        print("   - Model: GRU (faster than LSTM)")
        print("   - Data augmentation: DISABLED")
        print("   - Historical generation: SKIPPED")
        print("   - Cross-validation: DISABLED\n")

    config_file = "config.yaml"
    success_count = 0
    total_steps = 0

    print("\n" + "="*80)
    print("🚀 FOREX LSTM ПОКРАЩЕНИЙ PIPELINE")
    print("="*80)
    print(f"Час початку: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Тип моделі: {args.model_type}")
    print(f"Meta-ensemble: {'ТАК' if args.meta_ensemble else 'НІ'}")
    print(f"Data augmentation: {'НІ' if args.no_augment else 'ТАК'}")
    print(f"Focal loss: {'НІ' if args.no_focal_loss else 'ТАК'}")
    print(f"Cross-validation folds: {args.cv_folds}")
    print("="*80 + "\n")

    # STEP 1: Fetch MT5 Data
    if not args.skip_fetch:
        total_steps += 1
        if run_cmd(
            [sys.executable, "scripts/fetch_mt5.py", "--config", config_file],
            "КРОК 1: Завантаження даних з MetaTrader 5"
        ):
            success_count += 1
    else:
        print("\n⏭️  Пропущено: Завантаження даних з MT5")

    # STEP 2: Create Dataset with Walk-Forward Validation
    total_steps += 1
    if run_cmd(
        [sys.executable, "scripts/make_dataset.py", "--config", config_file, "--walk-forward"],
        "КРОК 2: Створення dataset з walk-forward validation та розширеними features"
    ):
        success_count += 1

    # STEP 3: Train Models
    total_steps += 1
    train_cmd = [sys.executable, "scripts/train_lstm.py", "--config", config_file]

    if args.model_type == "ensemble":
        train_cmd.append("--ensemble")
        description = "КРОК 3: Навчання ENSEMBLE моделей (LSTM + GRU + Attention)"
    else:
        train_cmd.extend(["--model-type", args.model_type])
        description = f"КРОК 3: Навчання {args.model_type.upper()} моделі"

    if args.no_augment:
        train_cmd.append("--no-augment")

    if args.no_focal_loss:
        train_cmd.append("--no-focal-loss")

    if run_cmd(train_cmd, description):
        success_count += 1

    # STEP 4: Generate Base Signals
    total_steps += 1
    if run_cmd(
        [sys.executable, "scripts/infer_signals.py", "--config", config_file, "--out", "outputs/signals.json"],
        "КРОК 4: Генерація базових торгових сигналів"
    ):
        success_count += 1

    # STEP 5: Historical Signal Generation (Optional)
    if not args.skip_history:
        total_steps += 1
        if run_cmd(
            [sys.executable, "historical_generator.py", "--config", config_file, "--days", str(args.history_days)],
            f"КРОК 5: Генерація історичних сигналів ({args.history_days} днів)"
        ):
            success_count += 1
    else:
        print("\n⏭️  Пропущено: Генерація історичних сигналів")

    # STEP 6: Label Generation
    if not args.skip_history:
        total_steps += 1
        if run_cmd(
            [sys.executable, "label_generator.py"],
            "КРОК 6: Створення labeled dataset для meta-моделі"
        ):
            success_count += 1

    # STEP 7: Train Meta-Model
    if not args.skip_history:
        total_steps += 1

        # Clean old meta-models
        print("\n🗑️  Видалення старих meta-моделей...")
        for f in glob.glob("models/meta_model_*.joblib"):
            os.remove(f)
            print(f"   Видалено: {f}")

        meta_cmd = [sys.executable, "train_meta_model.py", "--dataset", "meta_dataset.csv"]

        if args.meta_ensemble:
            meta_cmd.append("--ensemble")
            description = "КРОК 7: Навчання META-ENSEMBLE (LightGBM + XGBoost)"
        else:
            description = "КРОК 7: Навчання LightGBM meta-моделі"

        if args.cv_folds > 0:
            meta_cmd.extend(["--cv-folds", str(args.cv_folds)])
            description += f" з {args.cv_folds}-fold CV"

        if run_cmd(meta_cmd, description):
            success_count += 1

    # STEP 8: Generate Meta-Signals
    if not args.skip_history:
        total_steps += 1
        if run_cmd(
            [sys.executable, "infer_meta_signals.py", "--config", config_file],
            "КРОК 8: Генерація фінальних meta-сигналів"
        ):
            success_count += 1

    # STEP 9: Evaluate with Financial Metrics
    if not args.skip_history:
        total_steps += 1
        if run_cmd(
            [sys.executable, "evaluate_backtest.py", "--history-dir", "outputs/history", "--initial-balance", "10000"],
            "КРОК 9: Оцінка результатів з фінансовими метриками"
        ):
            success_count += 1

    # Final Summary
    print("\n" + "="*80)
    print("📊 ПІДСУМОК ВИКОНАННЯ PIPELINE")
    print("="*80)
    print(f"✅ Успішно виконано: {success_count}/{total_steps} кроків")
    print(f"⏱️  Час завершення: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if success_count == total_steps:
        print("\n🎉 ВСІ КРОКИ ВИКОНАНО УСПІШНО!")
        print("\n📁 Результати:")
        print("   - Моделі: models/")
        print("   - Сигнали: outputs/signals.json")
        if not args.skip_history:
            print("   - Meta-сигнали: outputs/meta_signal.json")
            print("   - Backtest звіт: outputs/backtest_report.json")
            print("   - Історія: outputs/history/")

        print("\n🌐 Для перегляду дашборду запустіть:")
        print("   codex run web")
        print("   або")
        print("   uvicorn scripts.web_server:app --host 0.0.0.0 --port 8000")
    else:
        print(f"\n⚠️  ЗАВЕРШЕНО З ПОМИЛКАМИ: {total_steps - success_count} кроків не виконано")
        sys.exit(1)

    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline перервано користувачем")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Критична помилка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
