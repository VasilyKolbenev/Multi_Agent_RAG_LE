# 🌐 Развертывание MultiAgent-RAG Pro

## 🚀 Способы публикации

### 1. Локальная сеть
```bash
python run_public.py
```
- ✅ Быстро и просто
- ✅ Бесплатно
- ❌ Только для локальной сети

### 2. ngrok (туннель в интернет)
```bash
python setup_ngrok.py
```
- ✅ Мгновенный публичный доступ
- ✅ HTTPS из коробки
- ❌ URL меняется при перезапуске
- ❌ Ограничения бесплатного плана

### 3. Railway (рекомендуется)
1. Создайте аккаунт на https://railway.app/
2. Подключите GitHub репозиторий
3. Добавьте переменную `OPENAI_API_KEY`
4. Railway автоматически развернет приложение

### 4. Render
1. Создайте аккаунт на https://render.com/
2. Создайте новый Web Service из GitHub
3. Настройки:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python run.py`
   - Environment Variables: `OPENAI_API_KEY`

### 5. Heroku
```bash
# Установите Heroku CLI
heroku create your-app-name
heroku config:set OPENAI_API_KEY=your_key
git push heroku main
```

### 6. DigitalOcean App Platform
1. Подключите GitHub репозиторий
2. Выберите план ($5/месяц)
3. Добавьте переменные окружения
4. Развертывание автоматическое

## 🔧 Настройка для продакшн

### Переменные окружения:
```bash
OPENAI_API_KEY=your_openai_key
LLM_PROVIDER=openai
LLM_MODEL=gpt-5-mini
LX_MODEL_ID=openai:gpt-5-mini
PORT=8000
```

### Безопасность:
- Используйте HTTPS
- Ограничьте доступ к API
- Настройте CORS для фронтенда
- Мониторинг использования API

## 📊 Сравнение платформ

| Платформа | Цена | Сложность | Время развертывания |
|-----------|------|-----------|-------------------|
| ngrok | Бесплатно* | Легко | 1 минута |
| Railway | $5/месяц | Легко | 5 минут |
| Render | Бесплатно* | Средне | 10 минут |
| Heroku | $7/месяц | Средне | 15 минут |
| DigitalOcean | $5/месяц | Сложно | 30 минут |

*Бесплатные планы имеют ограничения

## 🎯 Рекомендации

**Для демо/тестирования:** ngrok  
**Для небольших команд:** Railway или Render  
**Для продакшн:** DigitalOcean или AWS  

## 🔗 Полезные ссылки

- [Railway Docs](https://docs.railway.app/)
- [Render Docs](https://render.com/docs)
- [ngrok Docs](https://ngrok.com/docs)
- [Heroku Python](https://devcenter.heroku.com/articles/getting-started-with-python)
