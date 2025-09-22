# Руководство по развертыванию

## 🚀 GitHub Pages (Frontend)

### Автоматический деплой
1. Пуш в main/master ветку автоматически запускает деплой
2. GitHub Actions собирает React приложение
3. Результат публикуется на GitHub Pages

### Ручной деплой
```bash
cd react-ui
npm run deploy
git add ../docs-react
git commit -m "Deploy React UI"
git push
```

### Настройки GitHub Pages
- **Source**: Deploy from a branch
- **Branch**: main/master
- **Folder**: / (root) или /docs-react
- **URL**: `https://vasilykolbenev.github.io/Multi_Agent_RAG_LE/`

## 🚀 Railway (Backend)

### Автоматический деплой
1. Пуш в main/master ветку автоматически деплоится на Railway
2. Railway использует `railway_start.py` как entry point
3. Все переменные окружения настроены в Railway UI

### Переменные окружения Railway
```
OPENAI_API_KEY=sk-proj-...
LLM_MODEL=gpt-5-mini
EMBEDDING_MODEL=text-embedding-3-small
```

### URL API
- **Production**: `https://multiagentragle-production.up.railway.app`
- **Health check**: `https://multiagentragle-production.up.railway.app/health`

## 🔧 Локальная разработка

### Frontend
```bash
cd react-ui
npm install
npm run dev
# Открыть: http://localhost:3000
```

### Backend
```bash
cd server
pip install -r ../requirements.txt
python main.py
# API: http://localhost:8000
```

## 🌐 CORS настройки

Сервер настроен для работы с:
- ✅ `https://vasilykolbenev.github.io/Multi_Agent_RAG_LE/`
- ✅ `http://localhost:3000` (dev)
- ✅ `http://localhost:5173` (Vite)

## 📋 Checklist для деплоя

### Frontend (GitHub Pages)
- [ ] `vite.config.ts` имеет правильный `base: '/Multi_Agent_RAG_LE/'`
- [ ] `package.json` имеет скрипт `deploy`
- [ ] GitHub Actions настроен (`.github/workflows/deploy.yml`)
- [ ] GitHub Pages настроен в Settings репозитория

### Backend (Railway)
- [ ] `railway.toml` настроен
- [ ] `railway_start.py` существует
- [ ] CORS включает GitHub Pages URL
- [ ] Переменные окружения установлены в Railway
- [ ] Health endpoint возвращает `gpt-5-mini`

## 🧪 Тестирование

1. **Локально**: Запустите оба сервиса и протестируйте на `localhost:3000`
2. **Staging**: Протестируйте GitHub Pages с Railway API
3. **Production**: Полное тестирование на продакшн URLs

## 🔄 Workflow

1. Разработка локально
2. Коммит изменений
3. Пуш в main/master
4. Автоматический деплой на GitHub Pages и Railway
5. Тестирование на продакшн

Новый упрощенный интерфейс готов к развертыванию! 🎉
