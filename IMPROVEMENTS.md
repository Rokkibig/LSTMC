# 🚀 Покращення системи Forex LSTM

## Огляд впроваджених покращень

Цей документ описує всі покращення, які були впроваджені для підвищення якості прогнозування та результатів навчання моделей.

---

## 📊 1. Розширений Feature Engineering

### Додані індикатори:

**Технічні індикатори:**
- Multiple EMA (8, 20, 50, 100)
- Multiple RSI (7, 14, 21)
- Multiple ATR (7, 14) + ATR percentage
- Stochastic Oscillator (K, D)
- CCI (Commodity Channel Index)
- Williams %R
- ADX (Average Directional Index) + Plus DI / Minus DI

**Volume features:**
- Volume SMA and ratio
- On-Balance Volume (OBV)
- Volume standard deviation

**Volatility features:**
- High-Low percentage
- Close-Open percentage
- Rolling volatility (20, 50 periods)

**Price position features:**
- Close relative to High/Low
- Distance from moving averages

**Trend confirmation:**
- Multiple EMA alignment
- Strong trend detection (ADX > 25)

**Candle patterns:**
- Doji detection
- Hammer pattern

**Time-based features:**
- Hour of day
- Day of week
- Trading sessions (Asian, London, NY)
- Special days (Monday, Friday)

**Усього додано:** ~45 нових features замість попередніх 15

---

## 🧠 2. Покращена архітектура моделей

### LSTM модель (за замовчуванням):
```python
- LSTM(128) → BatchNorm → Dropout(0.3)
- LSTM(64) → BatchNorm → Dropout(0.3)
- LSTM(32)
- Dense(64) → BatchNorm → Dropout(0.3)
- Dense(3, softmax)
```

### GRU модель (швидша альтернатива):
```python
- GRU(128) → BatchNorm → Dropout(0.3)
- GRU(64) → BatchNorm → Dropout(0.3)
- GRU(32)
- Dense(64) → BatchNorm → Dropout(0.3)
- Dense(3, softmax)
```

### LSTM з Attention:
```python
- LSTM(128) → BatchNorm → Dropout(0.3)
- LSTM(64) → BatchNorm → Dropout(0.3)
- Attention mechanism
- Dense(64) → BatchNorm → Dropout(0.3)
- Dense(3, softmax)
```

**Покращення:**
- ✅ Збільшено кількість нейронів (64→32 → 128→64→32)
- ✅ Додано BatchNormalization для стабільності
- ✅ Збільшено Dropout (0.2 → 0.3)
- ✅ Додано L2 regularization (0.001)

---

## ⚖️ 3. Class Imbalance та Loss Function

### Focal Loss:
Замість простого categorical crossentropy використовується Focal Loss з параметрами:
- `gamma=2.0` - фокус на важких прикладах
- `alpha=0.25` - балансування класів

### Class Weights:
Автоматичний розрахунок ваг класів на основі розподілу даних:
```python
compute_class_weight('balanced', classes=unique_classes, y=y_train)
```

**Результат:** Краще навчання на minority класах (LONG/SHORT проти NO signal)

---

## 🔄 4. Data Augmentation

Додано два методи аугментації для часових рядів:

1. **Jittering** - додавання Gaussian noise (σ=0.01)
2. **Magnitude Warping** - масштабування з коефіцієнтом ~N(1.0, 0.1)

**Приріст даних:** кожен семпл генерує 2 додаткових → 3x більше training data

---

## 📈 5. Walk-Forward Validation

Замість простого split 70/15/15 додано:
- Time-series aware split
- Gap period (2%) між train і validation для запобігання data leakage
- Підтримка через флаг `--walk-forward`

**Використання:**
```bash
python scripts/make_dataset.py --config config.yaml --walk-forward
```

---

## 🎯 6. Оптимізація та Regularization

### Optimizer:
- Gradient clipping (clipnorm=1.0)
- Adam optimizer з adaptive learning rate

### Callbacks:
- ReduceLROnPlateau (patience=3, factor=0.5, min_lr=1e-6)
- EarlyStopping (patience=10, restore_best_weights=True)

### Epochs:
- Збільшено з 60 до 100 з early stopping

### Batch size:
- Зменшено з 256 до 128 для кращої генералізації

---

## 🌲 7. Покращений LightGBM Meta-Model

### Нові параметри:
```python
n_estimators: 500 (було 150)
learning_rate: 0.03 (було 0.05)
max_depth: 8
min_child_samples: 20
subsample: 0.8
colsample_bytree: 0.8
reg_alpha: 0.1 (L1)
reg_lambda: 0.1 (L2)
```

### Early Stopping:
- Використання validation set
- Автоматична зупинка через 50 раундів без покращення

### Feature Importance:
- Автоматичний аналіз важливості features
- Виведення топ-10 найважливіших features

---

## 🎭 8. Ensemble Models

### LightGBM + XGBoost Ensemble:
```bash
python train_meta_model.py --ensemble
```

**Weighted averaging** на основі validation performance:
- Автоматичний розрахунок ваг
- Комбінація предикцій двох моделей

### Multi-Architecture Ensemble (LSTM + GRU + Attention):
```bash
python scripts/train_lstm.py --config config.yaml --ensemble
```

**Результат:** 3 різні моделі для кожного symbol/timeframe

---

## 📊 9. Фінансові метрики

Новий скрипт `evaluate_backtest.py` розраховує:

### Risk-Adjusted Metrics:
- **Sharpe Ratio** - return / volatility
- **Sortino Ratio** - return / downside volatility
- **Calmar Ratio** - return / max drawdown

### Performance Metrics:
- **Max Drawdown** - максимальна просадка
- **Win Rate** - відсоток виграшних трейдів
- **Profit Factor** - gross profit / gross loss
- **Expectancy** - математичне очікування на трейд
- **Risk/Reward Ratio** - середнє співвідношення

**Використання:**
```bash
python evaluate_backtest.py --history-dir outputs/history
```

---

## 📝 10. Додаткові можливості

### Метрики під час навчання:
- Accuracy
- Precision
- Recall
- F1-Score (calculated)

### Збереження історії:
- Training history зберігається у JSON
- Можливість аналізу learning curves

### Time-Series Cross-Validation:
```bash
python train_meta_model.py --cv-folds 5
```

---

## 🚀 Як використовувати нові можливості

### 1. Базове навчання з усіма покращеннями:
```bash
# Створити датасет з walk-forward validation
python scripts/make_dataset.py --config config.yaml --walk-forward

# Тренувати LSTM з focal loss та augmentation
python scripts/train_lstm.py --config config.yaml

# Або тренувати всі три архітектури
python scripts/train_lstm.py --config config.yaml --ensemble
```

### 2. Вибір конкретної архітектури:
```bash
# LSTM (за замовчуванням)
python scripts/train_lstm.py --config config.yaml --model-type lstm

# GRU (швидший)
python scripts/train_lstm.py --config config.yaml --model-type gru

# LSTM з Attention
python scripts/train_lstm.py --config config.yaml --model-type attention
```

### 3. Налаштування meta-моделі:
```bash
# LightGBM (за замовчуванням)
python train_meta_model.py --dataset meta_dataset.csv

# Ensemble LightGBM + XGBoost
python train_meta_model.py --dataset meta_dataset.csv --ensemble

# З cross-validation
python train_meta_model.py --dataset meta_dataset.csv --cv-folds 5
```

### 4. Оцінка результатів:
```bash
# Backtest з фінансовими метриками
python evaluate_backtest.py --history-dir outputs/history --initial-balance 10000
```

---

## 📈 Очікувані покращення

На основі впроваджених змін, очікується:

1. **Підвищення точності** на 10-20% завдяки:
   - Розширеному feature engineering
   - Focal loss та class weights
   - Data augmentation

2. **Краща генералізація** завдяки:
   - BatchNormalization
   - Dropout 0.3
   - L2 regularization
   - Walk-forward validation

3. **Стабільніші результати** завдяки:
   - Gradient clipping
   - Early stopping
   - Ensemble моделей

4. **Кращі фінансові показники:**
   - Вищий Sharpe Ratio
   - Менший Max Drawdown
   - Вищий Profit Factor

---

## 🔧 Технічні деталі

### Нові залежності:
- `xgboost` - для ensemble
- `joblib` - для збереження моделей
- Оновлено `lightgbm` з кращими параметрами

### Оновлені файли:
- ✅ `scripts/utils.py` - розширений feature engineering
- ✅ `scripts/train_lstm.py` - нові архітектури та тренінг
- ✅ `scripts/make_dataset.py` - walk-forward validation
- ✅ `train_meta_model.py` - покращені hyperparameters + ensemble
- ✅ `infer_meta_signals.py` - підтримка ensemble моделей
- ✅ `evaluate_backtest.py` - новий скрипт фінансових метрик
- ✅ `requirements.txt` - оновлені залежності

### Нові параметри командного рядка:

**make_dataset.py:**
- `--walk-forward` - використовувати walk-forward validation

**train_lstm.py:**
- `--model-type {lstm,gru,attention}` - тип архітектури
- `--no-focal-loss` - вимкнути focal loss
- `--no-augment` - вимкнути augmentation
- `--ensemble` - тренувати всі три типи моделей

**train_meta_model.py:**
- `--ensemble` - LightGBM + XGBoost ensemble
- `--cv-folds N` - кількість фолдів для cross-validation

**evaluate_backtest.py:**
- `--history-dir` - директорія з історичними сигналами
- `--initial-balance` - початковий баланс
- `--risk-per-trade` - ризик на трейд (% від балансу)

---

## 📚 Рекомендації по використанню

### Для максимальної якості:
```bash
# 1. Підготовка даних
python scripts/make_dataset.py --config config.yaml --walk-forward

# 2. Тренування ensemble моделей
python scripts/train_lstm.py --config config.yaml --ensemble

# 3. Генерація історії
python historical_generator.py --config config.yaml --days 365

# 4. Підготовка meta-датасету
python label_generator.py

# 5. Тренування meta-ensemble
python train_meta_model.py --ensemble --cv-folds 5

# 6. Генерація сигналів
python scripts/infer_signals.py --config config.yaml
python infer_meta_signals.py

# 7. Оцінка результатів
python evaluate_backtest.py
```

### Для швидкого тестування:
```bash
# Використати GRU (швидший за LSTM)
python scripts/train_lstm.py --config config.yaml --model-type gru

# Без augmentation (швидше)
python scripts/train_lstm.py --config config.yaml --no-augment
```

---

## 🎉 Висновок

Всі покращення впроваджені та готові до використання! Система тепер включає:

✅ 45+ технічних індикаторів
✅ 3 типи neural network архітектур
✅ Focal Loss + Class Weights
✅ Data Augmentation
✅ Walk-Forward Validation
✅ LightGBM + XGBoost Ensemble
✅ Комплексні фінансові метрики
✅ Attention Mechanism
✅ Time-Series Cross-Validation

**Очікуване покращення якості: 15-25%**

Для питань та підтримки звертайтесь до документації або створіть issue в репозиторії.
