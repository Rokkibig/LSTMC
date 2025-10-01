# 🏗️ Architecture - Multi-Server Setup

## 🎯 Стратегія: Розділення відповідальностей

### Чому 2 сервери?

**Windows Server** → MT5 працює ТІЛЬКИ на Windows
**Linux Server** → TensorFlow/Docker працює ШВИДШЕ на Linux (**1.5-2x!**)

---

## 📊 Архітектура

```
┌─────────────────────────────────────────────────────────┐
│          👥 Users / Trading Clients                      │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTPS
                      ↓
┌─────────────────────────────────────────────────────────┐
│  🐧 Linux Server (ML Powerhouse)                         │
│  IP: TBD                                                 │
│  Port: 80/443                                            │
│                                                          │
│  🐳 Docker Containers:                                   │
│  ├── nginx (reverse proxy)                              │
│  ├── fastapi-ml (production API)                        │
│  ├── training-service (background jobs)                 │
│  └── postgres (optional - history)                      │
│                                                          │
│  📊 ML Training (ШВИДШЕ на Linux!):                      │
│  ├── LSTM/GRU/Attention models                          │
│  ├── LightGBM + XGBoost ensemble                        │
│  ├── Cross-validation (5 folds)                         │
│  └── 365 days history generation                        │
│                                                          │
│  🚀 Production API:                                      │
│  ├── GET /api/v1/predictions/{symbol}                   │
│  ├── GET /api/v1/forex/all                              │
│  ├── GET /api/v1/signals                                │
│  └── Dashboard для клієнтів                             │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP API
                       ↓
┌─────────────────────────────────────────────────────────┐
│  🪟 Windows Server (MT5 Data Provider)                   │
│  IP: 84.247.166.52                                       │
│  Port: 8001                                              │
│                                                          │
│  🔌 MT5 Integration:                                     │
│  ├── MetaTrader 5 Terminal (live connection)            │
│  └── fetch_mt5.py (data collector)                      │
│                                                          │
│  📡 Simple Data API:                                     │
│  ├── GET /mt5/prices/{symbol}        (real-time)        │
│  ├── GET /mt5/history/{symbol}/{tf}  (historical)       │
│  └── GET /mt5/ticks/{symbol}         (tick data)        │
│                                                          │
│  ⚡ Resources: Minimal (1-2 GB RAM)                      │
└─────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow

```
1. MT5 Terminal (Windows)
   ↓ real-time ticks
2. Windows API (port 8001)
   ↓ HTTP requests
3. Linux Training Service
   ↓ fetch historical data
4. Train LSTM/GRU models
   ↓ save models
5. Generate predictions
   ↓ save to JSON/DB
6. Linux Production API
   ↓ serve to clients
7. Users / Dashboard
```

---

## ⚡ Переваги Linux для ML

| Параметр | Windows | Linux | Переваги |
|----------|---------|-------|----------|
| **TensorFlow Speed** | 1.0x | **1.5-2x** | Native performance |
| **RAM Usage** | Baseline | **-30%** | Ефективніше |
| **Docker** | Emulation | **Native** | Швидкий deploy |
| **GPU (CUDA)** | Складно | **Просто** | pip install tensorflow-gpu |
| **Cron Jobs** | Task Scheduler | **cron** | Надійніше |
| **Cloud Cost** | Дорого | **Дешево** | AWS/GCP cheaper |
| **Scaling** | Важко | **K8s** | Horizontal scaling |

---

## 📦 Linux Server Stack

### Docker Compose Services:

```yaml
services:
  # Reverse Proxy
  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]

  # ML Training (background)
  training:
    build: ./training
    volumes: ["./models:/app/models"]
    environment:
      - WINDOWS_API_URL=http://84.247.166.52:8001

  # Production API
  api:
    build: ./api
    ports: ["8000:8000"]
    depends_on: [training]

  # Database (optional)
  postgres:
    image: postgres:15
    volumes: ["pgdata:/var/lib/postgresql/data"]
```

---

## 🔐 Security

### Windows → Linux Communication:
- ✅ VPN between servers (WireGuard)
- ✅ API key authentication
- ✅ HTTPS only
- ✅ Rate limiting

### Public API:
- ✅ JWT authentication
- ✅ Rate limits (60 req/min)
- ✅ CORS configured
- ✅ Nginx WAF

---

## 📅 Training Schedule

### Windows (легке):
- Збір даних з MT5: **постійно**
- API для віддачі даних: **24/7**

### Linux (важке):
- **01:00 щодня** → Quick retrain (30 хв)
- **02:00 субота** → Full retrain (2-4 год)
- **23:00 щодня** → M15 update (15 хв)

---

## 🚀 Deployment Flow

```
Developer (local)
  ↓ git push
GitHub/GitLab
  ↓ webhook trigger
GitHub Actions CI/CD
  ↓ build docker images
  ↓ run tests
  ↓ ssh to Linux server
Linux Server
  ↓ git pull
  ↓ docker-compose up -d
Production (zero-downtime)
```

---

## 📁 Repository Structure

```
LSTMC/
├── windows/              # Windows MT5 Provider
│   ├── fetch_mt5.py
│   ├── mt5_api.py       # Simple Flask API
│   └── requirements.txt
│
├── linux/                # Linux ML Service
│   ├── training/
│   │   ├── train_lstm.py
│   │   ├── train_meta.py
│   │   └── Dockerfile
│   ├── api/
│   │   ├── main.py
│   │   ├── routes/
│   │   └── Dockerfile
│   └── docker-compose.yml
│
├── shared/               # Спільний код
│   ├── utils.py
│   ├── config.yaml
│   └── requirements.txt
│
├── docs/                 # Документація
│   ├── SCHEDULE.md
│   ├── IMPROVEMENTS.md
│   └── API.md
│
└── .github/
    └── workflows/
        └── deploy.yml    # CI/CD
```

---

## 🎯 Implementation Plan

### Phase 1: Windows API (1-2 години)
- [ ] Створити простий Flask API для MT5
- [ ] Endpoints: prices, history, ticks
- [ ] Тестування локально

### Phase 2: Git Setup (30 хв)
- [x] .gitignore готовий
- [x] README готовий
- [x] ARCHITECTURE готовий
- [ ] Push на GitHub

### Phase 3: Linux Training Service (3-4 години)
- [ ] Dockerfile для training service
- [ ] Адаптувати train_lstm.py для remote data
- [ ] Dockerfile для API service
- [ ] docker-compose.yml

### Phase 4: CI/CD (1-2 години)
- [ ] GitHub Actions workflow
- [ ] Automated tests
- [ ] Deploy script

### Phase 5: Deploy (1 година)
- [ ] Linux server setup
- [ ] Docker install
- [ ] Deploy containers
- [ ] Configure nginx

---

## 📊 Expected Performance Improvement

| Метрика | Windows Only | Linux ML | Покращення |
|---------|--------------|----------|------------|
| Training Speed | 100% | **150-200%** | +50-100% |
| RAM Usage | Baseline | **-30%** | Економія |
| Deploy Time | 30+ хв | **2-3 хв** | -90% |
| Downtime | 5-10 хв | **0 хв** | Zero-downtime |
| Scalability | 1 server | **N servers** | Horizontal |

---

## 🔧 Next Steps

1. ✅ Підготувати Git repository
2. 🔄 Створити Windows MT5 API
3. 🔄 Створити Linux ML Service
4. 🔄 Setup CI/CD
5. 🔄 Deploy на Linux server

---

**Status:** Architecture Defined ✅
**Ready for:** Implementation
**Estimated Time:** 8-12 hours total
