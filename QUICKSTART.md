# 🚀 Швидкий старт - Покращений Forex LSTM

## 📦 Встановлення

```bash
# 1. Створіть віртуальне середовище
python -m venv .venv

# 2. Активуйте його (Windows)
.venv\Scripts\activate

# 3. Встановіть залежності
pip install -r requirements.txt
```

## ⚡ Швидкий тест (5-15 хвилин)

Для швидкого тестування покращень без довгого навчання:

```bash
# Windows
quick_test.bat

# Або вручну
python run_improved_pipeline.py --fast-mode --skip-fetch
```

**Що робить:**
- ✅ Створює dataset з walk-forward validation
- ✅ Тренує GRU модель (швидша за LSTM)
- ✅ Генерує торгові сигнали
- ⏭️ Пропускає історію та meta-моделі (для швидкості)

## 🎯 Повний pipeline (2-4+ години)

Для повного навчання з усіма покращеннями:

```bash
# Windows
full_improved_pipeline.bat

# Або вручну
python run_improved_pipeline.py --model-type ensemble --meta-ensemble --cv-folds 5
```

**Що робить:**
- ✅ Завантажує дані з MT5
- ✅ Створює dataset з 45+ індикаторами
- ✅ Тренує LSTM + GRU + Attention моделі
- ✅ Генерує історичні сигнали (365 днів)
- ✅ Тренує LightGBM + XGBoost meta-ensemble
- ✅ Виконує cross-validation
- ✅ Розраховує фінансові метрики

## 🎨 Гнучке використання

### Тренувати тільки один тип моделі:

```bash
# LSTM (за замовчуванням)
python run_improved_pipeline.py --model-type lstm

# GRU (швидший)
python run_improved_pipeline.py --model-type gru

# Attention LSTM
python run_improved_pipeline.py --model-type attention
```

### Без певних features:

```bash
# Без data augmentation
python run_improved_pipeline.py --no-augment

# Без focal loss
python run_improved_pipeline.py --no-focal-loss

# Без історії (швидше)
python run_improved_pipeline.py --skip-history
```

### Налаштування meta-моделі:

```bash
# Тільки LightGBM
python run_improved_pipeline.py

# LightGBM + XGBoost ensemble
python run_improved_pipeline.py --meta-ensemble

# З cross-validation
python run_improved_pipeline.py --cv-folds 5
```

## 📊 Перегляд результатів

### Запуск дашборду:

```bash
codex run web
# Або
uvicorn scripts.web_server:app --host 0.0.0.0 --port 8000
```

Відкрийте: http://127.0.0.1:8000

### Файли результатів:

- `outputs/signals.json` - Базові торгові сигнали
- `outputs/meta_signal.json` - Meta-сигнали (рекомендовані пари)
- `outputs/backtest_report.json` - Фінансові метрики
- `models/` - Натреновані моделі

## 🔧 Покрокове виконання

Якщо хочете контролювати кожен крок:

```bash
# 1. Завантажити дані
python scripts/fetch_mt5.py --config config.yaml

# 2. Створити dataset (з покращеннями)
python scripts/make_dataset.py --config config.yaml --walk-forward

# 3. Тренувати моделі
python scripts/train_lstm.py --config config.yaml --ensemble

# 4. Генерувати сигнали
python scripts/infer_signals.py --config config.yaml

# 5. (Опційно) Повний meta-pipeline
python historical_generator.py --config config.yaml --days 365
python label_generator.py
python train_meta_model.py --ensemble --cv-folds 5
python infer_meta_signals.py

# 6. Оцінити результати
python evaluate_backtest.py
```

## 📈 Що нового?

### Покращення моделей:
- ✅ **45+ технічних індикаторів** (було 15)
- ✅ **3 типи архітектур**: LSTM, GRU, Attention
- ✅ **Focal Loss** для class imbalance
- ✅ **Data Augmentation** (3x більше даних)
- ✅ **Walk-Forward Validation**
- ✅ **BatchNormalization + Dropout 0.3**

### Покращення meta-моделі:
- ✅ **LightGBM** з оптимізованими параметрами
- ✅ **XGBoost Ensemble**
- ✅ **Time-Series Cross-Validation**
- ✅ **Feature Importance** аналіз

### Нові метрики:
- ✅ **Sharpe Ratio**
- ✅ **Sortino Ratio**
- ✅ **Max Drawdown**
- ✅ **Profit Factor**
- ✅ **Win Rate**
- ✅ **Risk/Reward Ratio**

## 🆘 Допомога

### Всі параметри:

```bash
python run_improved_pipeline.py --help
```

### Проблеми:

1. **MT5 not connected** - Переконайтесь що MetaTrader 5 запущений
2. **Out of memory** - Використайте `--fast-mode` або зменшіть timeframes
3. **Too slow** - Використайте `--skip-history` або `--model-type gru`

### Детальна документація:

- `IMPROVEMENTS.md` - Повний опис всіх покращень
- `CLAUDE.md` - Команди та архітектура проекту
- `README.md` - Загальний огляд проекту

## 🎉 Швидкі команди

```bash
# Швидкий тест
python run_improved_pipeline.py --fast-mode --skip-fetch

# Середній режим (без історії)
python run_improved_pipeline.py --skip-history

# Повний режим
python run_improved_pipeline.py --model-type ensemble --meta-ensemble

# Тільки оцінка існуючих результатів
python evaluate_backtest.py --history-dir outputs/history
```

---

**Очікуване покращення якості: +15-25%**

Успішного трейдингу! 📈
