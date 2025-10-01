# 🪟 Windows MT5 Data Provider

Легкий API сервіс для віддачі даних з MetaTrader 5 на Linux сервер.

## 🎯 Роль

Windows Server виконує **ТІЛЬКИ одну функцію** - збирає дані з MT5 і віддає через HTTP API.

**Не робить:**
- ❌ Навчання моделей
- ❌ Генерація сигналів
- ❌ Важкі обчислення

**Робить:**
- ✅ Підключення до MT5
- ✅ Віддача real-time цін
- ✅ Віддача історичних даних
- ✅ Мінімальне навантаження (1-2 GB RAM)

---

## 🚀 Запуск

### Крок 1: Встановити залежності
```bash
pip install -r windows/requirements.txt
```

### Крок 2: Запустити MT5 Terminal
Переконайся що MT5 Terminal **запущений і залогінений**.

### Крок 3: Запустити API
```bash
windows\start_mt5_provider.bat
```

Або вручну:
```bash
python windows/mt5_data_provider.py
```

Сервіс запуститься на `http://0.0.0.0:5000`

---

## 📡 API Endpoints

### Health Check
```bash
GET http://84.247.166.52:5000/
GET http://84.247.166.52:5000/api/mt5/health
```

### Поточні ціни
```bash
# Одна пара
GET http://84.247.166.52:5000/api/mt5/price/EURUSD

# Всі пари
GET http://84.247.166.52:5000/api/mt5/prices
```

### Історичні дані
```bash
# 1 рік даних H1
GET http://84.247.166.52:5000/api/mt5/history/EURUSD/H1?years=1

# 5 років даних M15
GET http://84.247.166.52:5000/api/mt5/history/EURUSD/M15?years=5

# Обмежити кількість барів
GET http://84.247.166.52:5000/api/mt5/history/EURUSD/D1?years=20&limit=5000
```

Підтримувані таймфрейми:
- M1, M5, M15, M30
- H1, H2, H4
- D1, W1, MN1

### Список символів
```bash
GET http://84.247.166.52:5000/api/mt5/symbols
```

---

## 🔧 Конфігурація

Список символів береться з `config.yaml`:
```yaml
symbols:
  - EURUSD
  - GBPUSD
  - USDJPY
  # ...
```

---

## 🐛 Troubleshooting

### MT5 не підключається
```bash
# Перевір що MT5 Terminal запущений
tasklist | findstr terminal64.exe

# Перезапусти MT5
```

### Порт 5000 зайнятий
```bash
# Знайти процес
netstat -ano | findstr :5000

# Вбити процес
taskkill /F /PID <PID>
```

### Символ не знайдений
- Переконайся що символ є в Market Watch у MT5
- Права кнопка на символ → Show

---

## 📊 Ресурси

Цей сервіс **дуже легкий**:
- RAM: ~200-500 MB
- CPU: ~1-2%
- Disk: мінімально

Можна запускати на **слабкому комп'ютері** або навіть Raspberry Pi з Wine.

---

## 🔐 Безпека

**Для Production:**
1. Додай API ключ:
```python
API_KEY = "secret_key_123"

@app.before_request
def check_api_key():
    if request.headers.get("X-API-Key") != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
```

2. Обмеж доступ тільки з Linux IP:
```python
ALLOWED_IPS = ["<Linux server IP>"]

@app.before_request
def check_ip():
    if request.remote_addr not in ALLOWED_IPS:
        return jsonify({"error": "Forbidden"}), 403
```

3. Використовуй VPN (WireGuard) між Windows і Linux.

---

**Status:** Ready to use ✅
**Port:** 5000
**Resources:** Minimal
