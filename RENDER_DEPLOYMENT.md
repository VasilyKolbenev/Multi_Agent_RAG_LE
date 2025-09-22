# 🚀 Развертывание на Render.com

## Пошаговая инструкция

### 1. Подготовка репозитория

Убедитесь, что все файлы закоммичены:
```bash
git add .
git commit -m "Add Render.com deployment configuration"
git push
```

### 2. Создание сервиса на Render

1. Перейдите на [render.com](https://render.com)
2. Войдите через GitHub аккаунт
3. Нажмите **"New +"** → **"Web Service"**
4. Выберите ваш репозиторий `multiagent-rag-pro`

### 3. Настройки сервиса

**Основные настройки:**
- **Name**: `multiagent-rag-api`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python server/render_start.py`

**Advanced Settings:**
- **Auto-Deploy**: `Yes` (включить автодеплой)

### 4. Переменные окружения

В разделе **Environment Variables** добавьте:

```
OPENAI_API_KEY=sk-proj-ваш-ключ-здесь
LLM_MODEL=gpt-5-mini
EMBEDDING_MODEL=text-embedding-3-small
PORT=10000
```

⚠️ **Важно**: `OPENAI_API_KEY` нужно добавить обязательно!

### 5. Развертывание

1. Нажмите **"Create Web Service"**
2. Render автоматически начнет сборку
3. Процесс займет 5-10 минут
4. После завершения получите URL вида: `https://multiagent-rag-api.onrender.com`

### 6. Проверка работы

Откройте в браузере: `https://multiagent-rag-api.onrender.com/health`

Должны увидеть:
```json
{"ok": true, "model": "gpt-5-mini"}
```

### 7. Обновление фронтенда

После успешного деплоя обновите URL в React приложении (если нужно):

```bash
cd react-ui
# Если ваш Render URL отличается, обновите api.ts
npm run build
git add ../docs-react
git commit -m "Update API endpoint for Render"
git push
```

## 🔧 Файлы конфигурации

### `render.yaml`
Автоматическая конфигурация для Render (Infrastructure as Code)

### `server/render_start.py`
Entry point для Render с правильной настройкой портов

### Обновленные CORS
Добавлен `https://multiagent-rag-api.onrender.com` в разрешенные origins

## 🎯 Преимущества Render

- ✅ **Бесплатный план**: 750 часов/месяц
- ✅ **Автодеплой**: Из GitHub при каждом push
- ✅ **HTTPS**: Автоматический SSL сертификат
- ✅ **Логи**: Удобный просмотр логов
- ✅ **Переменные окружения**: Простое управление
- ✅ **Стабильность**: Более надежен чем Railway

## 🚨 Возможные проблемы

### Долгая сборка
- Render может собираться 5-10 минут при первом деплое
- Последующие деплои быстрее

### Холодный старт
- На бесплатном плане сервис засыпает после 15 минут неактивности
- Первый запрос после сна может занять 30-60 секунд

### Решение для холодного старта
Можно настроить ping каждые 10 минут через GitHub Actions:

```yaml
# .github/workflows/keep-alive.yml
name: Keep Render Service Alive
on:
  schedule:
    - cron: '*/10 * * * *'  # Каждые 10 минут
jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - run: curl https://multiagent-rag-api.onrender.com/health
```

## 🔄 Workflow

1. **Разработка** → локально
2. **Коммит** → в GitHub
3. **Автодеплой** → на Render
4. **Тестирование** → на продакшн URL

Готово! Ваше приложение теперь на Render.com 🎉
