# 🚀 CI/CD Pipeline

Автоматичний deploy на Linux server через GitHub Actions.

## 📋 Як працює

При `git push` на `main`:
1. ✅ **Test** - Запускає тести і лінтинг
2. ✅ **Build** - Збирає Docker image
3. ✅ **Deploy** - Деплоїть на Linux server
4. ❌ **Rollback** - Автоматичний откат при помилці

---

## 🔐 Налаштування Secrets

В GitHub repository → Settings → Secrets and variables → Actions:

### Required Secrets:

1. **SSH_PRIVATE_KEY**
   ```bash
   # Створити SSH ключ на локальному комп'ютері
   ssh-keygen -t ed25519 -C "github-actions@forex-ml" -f ~/.ssh/forex_deploy

   # Скопіювати ПРИВАТНИЙ ключ
   cat ~/.ssh/forex_deploy

   # Додати в GitHub Secrets → SSH_PRIVATE_KEY
   ```

2. **SSH_PUBLIC_KEY** (додати на Linux server)
   ```bash
   # Скопіювати ПУБЛІЧНИЙ ключ
   cat ~/.ssh/forex_deploy.pub

   # Додати на Linux server
   ssh user@your-server
   echo "вміст_публічного_ключа" >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   ```

3. **SERVER_HOST**
   ```
   Приклад: 123.45.67.89
   Або: your-server.com
   ```

4. **SERVER_USER**
   ```
   Приклад: ubuntu
   Або: root
   ```

5. **DEPLOY_PATH**
   ```
   Приклад: /home/ubuntu/LSTMC
   Або: /opt/forex-ml
   ```

---

## 🎯 Ручний запуск

GitHub → Actions → Deploy to Linux Server → Run workflow

---

## 📊 Процес деплою

```
Developer
  ↓ git push origin main
GitHub Repository
  ↓ trigger webhook
GitHub Actions
  ↓ run tests
  ↓ build docker image
  ↓ ssh to server
Linux Server
  ↓ git pull
  ↓ docker-compose down
  ↓ docker load new image
  ↓ docker-compose up -d
Production (zero-downtime)
```

---

## 🐛 Troubleshooting

### SSH Connection Failed
```bash
# Перевір SSH ключ на сервері
ssh -i ~/.ssh/forex_deploy user@server

# Перевір authorized_keys
cat ~/.ssh/authorized_keys
```

### Docker Build Failed
```bash
# Перевір Dockerfile локально
cd linux
docker build -t test .
```

### Deployment Failed - Rollback
Workflow автоматично робить rollback до попередньої версії при помилці.

### Manual Rollback
```bash
# Підключись до сервера
ssh user@server
cd /path/to/LSTMC

# Відкат на 1 коміт назад
git reset --hard HEAD~1
docker-compose -f linux/docker-compose.yml down
docker-compose -f linux/docker-compose.yml up -d
```

---

## ✅ Перевірка після деплою

```bash
# На сервері
docker-compose -f linux/docker-compose.yml ps
docker-compose -f linux/docker-compose.yml logs -f

# З локального комп'ютера
curl http://your-server:8000/health
```

---

## 🔧 Додаткові налаштування

### Notifications (Slack/Discord)
Додати в кінці `deploy.yml`:
```yaml
- name: Notify Slack
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
    payload: |
      {"text": "Deployment ${{ job.status }}!"}
```

### Multiple Environments
Створити окремі workflows:
- `deploy-staging.yml` - для тестування
- `deploy-production.yml` - для production

---

**Status:** Configured ✅
**Auto-deploy:** Enabled 🚀
**Rollback:** Automatic ⏪
