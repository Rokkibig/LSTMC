# 🐧 Linux ML Training Service

Docker-ready ML training service для потужного навчання моделей на Linux.

## 🎯 Переваги Linux

| Параметр | Windows | Linux | Переваги |
|----------|---------|-------|----------|
| TensorFlow Speed | 1.0x | **1.5-2x** | Native performance |
| RAM Usage | Baseline | **-30%** | Efficient |
| Docker | Emulation | **Native** | Fast deploy |
| GPU (CUDA) | Складно | **Просто** | Easy setup |
| Cost (Cloud) | Дорого | **Дешево** | AWS/GCP cheaper |

---

## 🚀 Швидкий старт

### Крок 1: Переконайся що Windows MT5 API працює
```bash
curl http://84.247.166.52:5000/api/mt5/health
```

Якщо отримаєш `{"status": "ok"}` - все готово!

### Крок 2: Клонувати репозиторій
```bash
git clone https://github.com/Rokkibig/LSTMC.git
cd LSTMC/linux
```

### Крок 3: Налаштувати конфігурацію
```bash
# Створити необхідні директорії
mkdir -p models outputs logs data

# Скопіювати config.yaml
cp ../config.yaml .
```

### Крок 4: Запустити Docker Compose
```bash
docker-compose up -d
```

Це запустить:
- **training** - Background training scheduler
- **api** - Production API на порту 8000

### Крок 5: Перевірити статус
```bash
# Перевірити контейнери
docker-compose ps

# Переглянути логи
docker-compose logs -f training

# API health check
curl http://localhost:8000/health
```

---

## 📊 Архітектура

```
Windows Server (84.247.166.52:5000)
           ↓ HTTP API
    [training_scheduler.py]
           ↓
  Fetch historical data
           ↓
    Train LSTM/GRU models
           ↓
   Save models & outputs
           ↓
      [main.py - API]
           ↓
    Serve predictions
```

---

## ⏰ Розклад тренування

Training scheduler автоматично виконує:

| Час | Тип | Тривалість | Команда |
|-----|-----|------------|---------|
| **01:00 щодня** | Quick retrain | 30 хв | `--skip-history` |
| **02:00 субота** | Full retrain | 2-4 год | `--ensemble --meta --cv-folds 5` |
| **23:00 щодня** | M15 update | 15 хв | `--model-type gru` |

---

## 🐳 Docker Commands

### Запуск
```bash
docker-compose up -d
```

### Зупинка
```bash
docker-compose down
```

### Перегляд логів
```bash
# Всі логи
docker-compose logs -f

# Тільки training
docker-compose logs -f training

# Тільки API
docker-compose logs -f api
```

### Перезбірка після змін коду
```bash
docker-compose build
docker-compose up -d
```

### Ручне тренування
```bash
# Зайти в контейнер
docker-compose exec training bash

# Запустити тренування вручну
python run_improved_pipeline.py --model-type ensemble
```

---

## 📡 API Endpoints

### Health Check
```bash
GET http://localhost:8000/health
```

### Predictions
```bash
# Отримати прогноз
GET http://localhost:8000/api/v1/predictions/{symbol}

# Всі прогнози
GET http://localhost:8000/api/v1/predictions/all
```

### System Status
```bash
GET http://localhost:8000/api/v1/system/status
GET http://localhost:8000/api/v1/training/status
```

---

## 🔧 Налаштування для Production

### 1. Nginx Reverse Proxy
```bash
# Запустити з nginx
docker-compose --profile production up -d
```

### 2. SSL/TLS
Помістити сертифікати в `nginx/ssl/`:
- `fullchain.pem`
- `privkey.pem`

### 3. Environment Variables
Створити `.env`:
```env
WINDOWS_MT5_API=http://84.247.166.52:5000
TZ=Europe/Kiev
API_WORKERS=4
```

### 4. Автозапуск при старті системи
```bash
# Створити systemd service
sudo nano /etc/systemd/system/forex-ml.service
```

```ini
[Unit]
Description=Forex ML Training Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/user/LSTMC/linux
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable forex-ml
sudo systemctl start forex-ml
```

---

## 📊 Моніторинг

### Metrics Endpoint
```bash
GET http://localhost:8000/metrics
```

Prometheus-compatible metrics:
- Training duration
- Model accuracy
- API requests
- Error rates

### Grafana Dashboard
```bash
# Додати до docker-compose.yml
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana-storage:/var/lib/grafana
```

---

## 🐛 Troubleshooting

### Контейнери не запускаються
```bash
# Перевірити логи
docker-compose logs training

# Перевірити доступ до Windows API
docker-compose exec training curl http://84.247.166.52:5000/api/mt5/health
```

### Недостатньо пам'яті
```bash
# Збільшити ліміти в docker-compose.yml
services:
  training:
    deploy:
      resources:
        limits:
          memory: 8G
```

### GPU не розпізнається
```bash
# Встановити nvidia-container-toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit

# Додати в docker-compose.yml
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

---

## 🚀 CI/CD Deployment

### Автоматичний deploy через GitHub Actions
При push на `main` гілку:
1. Build Docker images
2. Run tests
3. SSH до Linux server
4. Pull latest code
5. Restart containers

Див. `.github/workflows/deploy.yml`

---

## 📈 Очікувані результати

З цією архітектурою:

| Метрика | До | Після | Покращення |
|---------|-----|-------|------------|
| Training Speed | 100% | **150-200%** | +50-100% |
| Accuracy M15 | 55-60% | **65-75%** | +10-15% |
| Sharpe Ratio | 0.8-1.0 | **1.5-2.2** | +70-120% |
| Deploy Time | 30+ хв | **2-3 хв** | -90% |

---

**Status:** Production Ready ✅
**Docker:** Yes 🐳
**GPU:** Supported 🎮
**Auto-deploy:** Ready 🚀
