# 📚 Документація - Покращений Forex LSTM

## 🚀 Швидкий старт

Якщо ви тільки почали, почніть з:

1. **[QUICKSTART.md](QUICKSTART.md)** - Покрокова інструкція для початківців
2. **[EXAMPLES.md](EXAMPLES.md)** - Практичні приклади використання

## 📖 Основна документація

### Для користувачів:

- **[README.md](README.md)** - Загальний огляд проекту
- **[QUICKSTART.md](QUICKSTART.md)** - Швидкий старт за 5 хвилин
- **[EXAMPLES.md](EXAMPLES.md)** - Приклади різних сценаріїв використання
- **[BEFORE_AFTER.md](BEFORE_AFTER.md)** - Порівняння до/після покращень

### Для розробників:

- **[CLAUDE.md](CLAUDE.md)** - Команди та архітектура для Claude Code
- **[IMPROVEMENTS.md](IMPROVEMENTS.md)** - Детальний технічний опис покращень
- **[SUMMARY.md](SUMMARY.md)** - Короткий підсумок всіх змін

### Для менеджерів:

- **[SUMMARY.md](SUMMARY.md)** - Що зроблено (executive summary)
- **[BEFORE_AFTER.md](BEFORE_AFTER.md)** - Візуальне порівняння результатів

---

## 🗂️ Структура документації

```
📁 Документація
│
├── 🚀 Швидкий старт
│   ├── QUICKSTART.md          ← Почати тут!
│   └── EXAMPLES.md            ← Приклади
│
├── 📊 Огляд
│   ├── README.md              ← Що це за проект?
│   ├── SUMMARY.md             ← Що зроблено?
│   └── BEFORE_AFTER.md        ← Порівняння
│
├── 🔧 Технічна документація
│   ├── IMPROVEMENTS.md        ← Детальний опис
│   └── CLAUDE.md              ← Команди
│
└── 📚 Цей файл
    └── INDEX.md               ← Ви тут
```

---

## 🎯 Навігація за задачами

### "Я хочу почати використовувати"
→ [QUICKSTART.md](QUICKSTART.md)

### "Я хочу зрозуміти що змінилось"
→ [BEFORE_AFTER.md](BEFORE_AFTER.md)

### "Я хочу побачити приклади команд"
→ [EXAMPLES.md](EXAMPLES.md)

### "Я хочу знати технічні деталі"
→ [IMPROVEMENTS.md](IMPROVEMENTS.md)

### "Я хочу короткий підсумок"
→ [SUMMARY.md](SUMMARY.md)

### "Я розробник і хочу команди"
→ [CLAUDE.md](CLAUDE.md)

---

## 📝 Швидкі посилання

### Основні команди:

```bash
# Швидкий тест
python run_improved_pipeline.py --fast-mode --skip-fetch

# Повний pipeline
python run_improved_pipeline.py --model-type ensemble --meta-ensemble

# Dashboard
codex run web
```

### Основні файли:

- `run_improved_pipeline.py` - Головний скрипт
- `quick_test.bat` - Швидкий тест (Windows)
- `full_improved_pipeline.bat` - Повний pipeline (Windows)
- `config.yaml` - Конфігурація

### Результати:

- `outputs/signals.json` - Базові сигнали
- `outputs/meta_signal.json` - Meta-сигнали
- `outputs/backtest_report.json` - Фінансові метрики
- `models/` - Натреновані моделі

---

## 🎓 Навчальний трек

### Рівень 1: Початківець
1. Прочитати [README.md](README.md)
2. Встановити залежності (дивись [QUICKSTART.md](QUICKSTART.md))
3. Запустити швидкий тест: `python run_improved_pipeline.py --fast-mode`
4. Подивитись результати в `outputs/`

### Рівень 2: Користувач
1. Прочитати [EXAMPLES.md](EXAMPLES.md)
2. Запустити різні конфігурації
3. Порівняти результати різних моделей
4. Налаштувати під свої потреби

### Рівень 3: Експерт
1. Прочитати [IMPROVEMENTS.md](IMPROVEMENTS.md)
2. Модифікувати features в `scripts/utils.py`
3. Експериментувати з hyperparameters
4. Створювати власні архітектури

---

## 🔍 Пошук по темах

### Architecture
- [IMPROVEMENTS.md § 2](IMPROVEMENTS.md#-2-покращена-архітектура-моделей) - Архітектури моделей
- [BEFORE_AFTER.md § Architecture](BEFORE_AFTER.md#-архітектура-моделі) - Порівняння архітектур

### Features
- [IMPROVEMENTS.md § 1](IMPROVEMENTS.md#-1-розширений-feature-engineering) - Feature engineering
- [BEFORE_AFTER.md § Features](BEFORE_AFTER.md#-feature-engineering) - Порівняння features

### Training
- [IMPROVEMENTS.md § 3-6](IMPROVEMENTS.md#-3-class-imbalance-та-loss-function) - Процес навчання
- [EXAMPLES.md § Monitoring](EXAMPLES.md#7️⃣-моніторинг-навчання) - Моніторинг

### Meta-Learning
- [IMPROVEMENTS.md § 7-8](IMPROVEMENTS.md#-7-покращений-lightgbm-meta-model) - Meta-моделі
- [EXAMPLES.md § Meta-model](EXAMPLES.md#5️⃣-налаштування-meta-моделі) - Приклади

### Evaluation
- [IMPROVEMENTS.md § 9](IMPROVEMENTS.md#-9-фінансові-метрики) - Метрики
- [EXAMPLES.md § Backtest](EXAMPLES.md#6️⃣-backtest-та-evaluation) - Backtest

### Automation
- [IMPROVEMENTS.md § 10](IMPROVEMENTS.md#-10-додаткові-можливості) - Automation
- [EXAMPLES.md § Production](EXAMPLES.md#-production-deployment) - Deployment

---

## 📊 Зміст файлів

### README.md
```
- Огляд проекту
- Архітектура
- Quick steps
- API endpoints
- Project layout
```

### QUICKSTART.md
```
- Встановлення (3 кроки)
- Швидкий тест (5-15 хв)
- Повний pipeline (2-4 год)
- Гнучке використання
- Перегляд результатів
- Покрокове виконання
- Що нового?
- Допомога
```

### IMPROVEMENTS.md
```
- 10 категорій покращень
- Технічні деталі
- Приклади коду
- Параметри командного рядка
- Очікувані результати
- Інструкції по використанню
```

### SUMMARY.md
```
- Чеклист виконаного
- Короткий опис кожного пункту
- Таблиця покращень
- Статус проекту
- Наступні кроки
```

### BEFORE_AFTER.md
```
- Таблиця порівнянь
- Детальне порівняння по категоріях
- Візуальне представлення
- Очікувані результати
```

### EXAMPLES.md
```
- 10 сценаріїв використання
- Практичні приклади команд
- Code snippets
- Troubleshooting
- Pro tips
```

### CLAUDE.md
```
- Команди для розробки
- Архітектура системи
- Data flow
- Development guidelines
```

---

## 🆘 Де шукати допомогу?

### "У мене не працює команда X"
→ [EXAMPLES.md](EXAMPLES.md) секція "Debugging"

### "Як налаштувати параметр Y?"
→ [IMPROVEMENTS.md](IMPROVEMENTS.md) секція відповідного покращення

### "Що означає ця помилка?"
→ [EXAMPLES.md](EXAMPLES.md) секція "Troubleshooting"

### "Як покращити результати?"
→ [IMPROVEMENTS.md](IMPROVEMENTS.md) секція "Рекомендації"

### "Яка команда для Z?"
→ [QUICKSTART.md](QUICKSTART.md) або [EXAMPLES.md](EXAMPLES.md)

---

## 🎉 Швидкі факти

- **15 → 45+ features** (Feature engineering)
- **1 → 3 архітектури** (LSTM, GRU, Attention)
- **1 → 2 ensemble** (Neural + Gradient Boosting)
- **1 → 8 метрик** (Фінансова аналітика)
- **8 → 1 команд** (Automation)
- **+15-25%** очікуване покращення

---

## 📞 Контакти та підтримка

- **Issues**: GitHub Issues (якщо є репозиторій)
- **Documentation**: Ці файли
- **Updates**: Перевірте CHANGELOG.md (якщо є)

---

## 🗺️ Дорожня карта

### Поточна версія: 2.0 (Improved)
- ✅ Всі 10 покращень впроваджені
- ✅ Automation scripts готові
- ✅ Документація завершена

### Можливі майбутні покращення:
- 🔮 Transformer architecture
- 🔮 Reinforcement Learning
- 🔮 Multi-asset portfolio optimization
- 🔮 Real-time inference API
- 🔮 Cloud deployment
- 🔮 Web-based training dashboard

---

**Дякуємо за використання покращеного Forex LSTM!** 🚀

Успішного трейдингу! 📈💰
