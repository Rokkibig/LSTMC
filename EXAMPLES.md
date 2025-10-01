# 📚 Приклади використання покращеного pipeline

## 🎯 Сценарії використання

---

## 1️⃣ Перший запуск (Новий користувач)

### Мета: Швидко перевірити чи все працює

```bash
# Крок 1: Встановити залежності
pip install -r requirements.txt

# Крок 2: Швидкий тест (5-15 хвилин)
python run_improved_pipeline.py --fast-mode --skip-fetch

# Крок 3: Переглянути результати
python -c "import json; print(json.dumps(json.load(open('outputs/signals.json')), indent=2)[:500])"
```

**Що відбувається:**
- ✅ Використовує існуючі дані
- ✅ Тренує GRU (швидкий)
- ✅ Без augmentation
- ✅ Без історії
- ⏱️ ~5-15 хвилин

---

## 2️⃣ Продакшн режим (Максимальна якість)

### Мета: Натренувати найкращі моделі

```bash
# Повний pipeline з усіма покращеннями
python run_improved_pipeline.py \
    --model-type ensemble \
    --meta-ensemble \
    --cv-folds 5 \
    --history-days 365

# Або просто
full_improved_pipeline.bat  # Windows
```

**Що відбувається:**
- ✅ Завантажує свіжі дані з MT5
- ✅ 45+ features
- ✅ Тренує LSTM + GRU + Attention
- ✅ Data augmentation (3x data)
- ✅ Walk-forward validation
- ✅ LightGBM + XGBoost ensemble
- ✅ 5-fold cross-validation
- ✅ 365 днів історії
- ✅ Фінансові метрики
- ⏱️ ~2-4+ години

---

## 3️⃣ Дослідження архітектур

### Мета: Порівняти різні моделі

```bash
# Тренувати LSTM
python scripts/train_lstm.py --config config.yaml --model-type lstm
# Результат: models/*_lstm.h5

# Тренувати GRU
python scripts/train_lstm.py --config config.yaml --model-type gru
# Результат: models/*_gru.h5

# Тренувати Attention
python scripts/train_lstm.py --config config.yaml --model-type attention
# Результат: models/*_attention.h5

# Порівняти за історією навчання
python -c "
import json, glob
for f in glob.glob('models/*_history.json'):
    with open(f) as fp:
        h = json.load(fp)
        print(f'{f}: val_loss={h[\"val_loss\"][-1]:.4f}, val_accuracy={h[\"val_accuracy\"][-1]:.4f}')
"
```

---

## 4️⃣ Оптимізація швидкості

### Мета: Швидше навчання для експериментів

```bash
# Варіант 1: GRU без augmentation
python run_improved_pipeline.py \
    --model-type gru \
    --no-augment \
    --skip-history

# Варіант 2: LSTM але без історії
python run_improved_pipeline.py \
    --model-type lstm \
    --skip-history

# Варіант 3: Fast mode
python run_improved_pipeline.py --fast-mode
```

**Порівняння швидкості:**
- Full mode: ~3-4 години
- Skip history: ~30-60 хвилин
- No augment: ~20-40 хвилин
- GRU: -30% часу від LSTM
- Fast mode: ~5-15 хвилин

---

## 5️⃣ Налаштування Meta-моделі

### Мета: Експерименти з meta-learning

```bash
# Базова LightGBM
python train_meta_model.py --dataset meta_dataset.csv

# Ensemble (LightGBM + XGBoost)
python train_meta_model.py --dataset meta_dataset.csv --ensemble

# З cross-validation
python train_meta_model.py --dataset meta_dataset.csv --cv-folds 5

# Все разом
python train_meta_model.py --dataset meta_dataset.csv --ensemble --cv-folds 5
```

**Результати:**
```
models/
├── meta_model_EUR.joblib
├── meta_model_GBP.joblib
├── meta_model_JPY.joblib
├── meta_model_CHF.joblib
├── meta_model_AUD.joblib
├── meta_model_CAD.joblib
└── meta_model_NZD.joblib
```

---

## 6️⃣ Backtest та Evaluation

### Мета: Оцінити фінансові результати

```bash
# Базовий backtest
python evaluate_backtest.py --history-dir outputs/history

# З кастомними параметрами
python evaluate_backtest.py \
    --history-dir outputs/history \
    --initial-balance 50000 \
    --risk-per-trade 0.01

# Переглянути звіт
cat outputs/backtest_report.json
```

**Приклад виводу:**
```
============================================================
BACKTEST RESULTS
============================================================
Initial Balance:    $10,000.00
Final Balance:      $15,234.56
Total Return:       +52.35%
Total Trades:       245
Win Rate:           58.37%

PERFORMANCE METRICS
------------------------------------------------------------
Sharpe Ratio:       1.834
Sortino Ratio:      2.156
Max Drawdown:       18.23%
Calmar Ratio:       2.873
Profit Factor:      1.982
Expectancy:         $21.36
Risk/Reward Ratio:  1.753
============================================================
```

---

## 7️⃣ Моніторинг навчання

### Мета: Відстежувати прогрес під час навчання

```bash
# Terminal 1: Запустити навчання
python scripts/train_lstm.py --config config.yaml --ensemble

# Terminal 2: Моніторити log файли (якщо є)
# Або переглянути історію після завершення
python -c "
import json, matplotlib.pyplot as plt

with open('models/EURUSD_D1_lstm_history.json') as f:
    h = json.load(f)

plt.figure(figsize=(12, 4))
plt.subplot(1, 2, 1)
plt.plot(h['loss'], label='Train Loss')
plt.plot(h['val_loss'], label='Val Loss')
plt.legend()
plt.title('Loss')

plt.subplot(1, 2, 2)
plt.plot(h['accuracy'], label='Train Acc')
plt.plot(h['val_accuracy'], label='Val Acc')
plt.legend()
plt.title('Accuracy')

plt.savefig('training_curves.png')
print('Saved to training_curves.png')
"
```

---

## 8️⃣ Інкрементальне навчання

### Мета: Додати нові дані без повного перенавчання

```bash
# Крок 1: Завантажити нові дані
python scripts/fetch_mt5.py --config config.yaml

# Крок 2: Оновити dataset
python scripts/make_dataset.py --config config.yaml --walk-forward

# Крок 3: Перетренувати тільки одну модель
python scripts/train_lstm.py --config config.yaml --model-type lstm

# Крок 4: Оновити сигнали
python scripts/infer_signals.py --config config.yaml
```

---

## 9️⃣ Debugging та Troubleshooting

### Мета: Знайти та виправити проблеми

```bash
# Перевірити дані
python -c "
import pandas as pd
import glob

for f in glob.glob('data/*_D1.csv'):
    df = pd.read_csv(f)
    print(f'{f}: {len(df)} rows, {df.columns.tolist()[:5]}...')
"

# Перевірити моделі
python -c "
import glob, os

for f in glob.glob('models/*.h5'):
    size = os.path.getsize(f) / 1024 / 1024
    print(f'{f}: {size:.2f} MB')
"

# Перевірити features
python scripts/make_dataset.py --config config.yaml --walk-forward
# Подивитись на _meta.json файли
python -c "
import json
with open('data/EURUSD_D1_meta.json') as f:
    meta = json.load(f)
    print(f'Features ({len(meta[\"features\"])}): {meta[\"features\"][:10]}...')
"
```

---

## 🔟 Production Deployment

### Мета: Налаштувати для постійної роботи

```bash
# Windows Task Scheduler
# Створити task, що запускає кожен день о 00:00:

# full_retrain.bat:
@echo off
cd D:\LLM\LSTMC
call .venv\Scripts\activate
python run_improved_pipeline.py --skip-history >> logs/daily.log 2>&1

# Або тільки inference без retraining:
# daily_signals.bat:
@echo off
cd D:\LLM\LSTMC
call .venv\Scripts\activate
python scripts/fetch_mt5.py --config config.yaml
python scripts/infer_signals.py --config config.yaml
python infer_meta_signals.py --config config.yaml
```

---

## 🎨 Кастомізація

### Приклад 1: Тільки певні символи

```python
# custom_config.yaml
symbols:
  - EURUSD
  - GBPUSD
timeframes:
  H1:
    years: 10
    seq_len: 96
    horizon: 6
```

```bash
python run_improved_pipeline.py --config custom_config.yaml
```

### Приклад 2: Власні hyperparameters

Відредагуйте `scripts/train_lstm.py`:
```python
# Знайти build_lstm_model() та змінити:
layers.LSTM(256, ...)  # Було 128
layers.Dropout(0.4)     # Було 0.3
```

### Приклад 3: Додати новий індикатор

Відредагуйте `scripts/utils.py`:
```python
def make_features(df):
    # ... існуючий код ...

    # Додати свій індикатор
    out["MyIndicator"] = your_calculation(out["Close"])

    return out.dropna().reset_index(drop=True)
```

---

## 📊 Dashboard та Visualization

```bash
# Запустити web dashboard
codex run web
# або
uvicorn scripts.web_server:app --host 0.0.0.0 --port 8000

# Відкрити в браузері
# http://127.0.0.1:8000

# API endpoints:
curl http://127.0.0.1:8000/api/signals
curl http://127.0.0.1:8000/api/prices
```

---

## 💡 Pro Tips

### 1. Паралельне навчання різних моделей

```bash
# Terminal 1
python scripts/train_lstm.py --config config.yaml --model-type lstm

# Terminal 2
python scripts/train_lstm.py --config config.yaml --model-type gru

# Terminal 3
python scripts/train_lstm.py --config config.yaml --model-type attention
```

### 2. Automatic retraining script

```bash
# auto_retrain.sh
#!/bin/bash
while true; do
    echo "[$(date)] Starting retraining..."
    python run_improved_pipeline.py --skip-history
    echo "[$(date)] Retraining complete. Sleeping 24h..."
    sleep 86400
done
```

### 3. Email notifications (опціонально)

```python
# Додати в кінець run_improved_pipeline.py
import smtplib
from email.message import EmailMessage

def send_notification(subject, body):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = 'your@email.com'
    msg['To'] = 'recipient@email.com'
    msg.set_content(body)

    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login('your@email.com', 'password')
        smtp.send_message(msg)

# В кінці main():
send_notification('Pipeline Complete', f'Success: {success_count}/{total_steps}')
```

---

## 🆘 Часті проблеми

### Проблема: Out of Memory

```bash
# Рішення: Зменшити batch size або використати менше timeframes
python scripts/train_lstm.py --config config.yaml --model-type gru --no-augment
```

### Проблема: MT5 connection failed

```bash
# Рішення: Переконайтесь що MT5 запущений
# Або пропустіть fetch
python run_improved_pipeline.py --skip-fetch
```

### Проблема: Training too slow

```bash
# Рішення: Використайте fast mode або GRU
python run_improved_pipeline.py --fast-mode
```

---

Успішного використання! 🚀📈
