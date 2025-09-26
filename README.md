# 🤖 MultiAgent-RAG Pro

**Многоагентная система для работы с документами на базе GPT-5-mini**

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/multiagent-rag-pro)

## ✨ Возможности

- 🧠 **Многоагентная архитектура**: Планировщик → Писатель → Критик
- 📚 **RAG система**: Поиск и анализ документов с цитированием источников
- 🏷️ **Извлечение сущностей**: LangExtract для автоматического выделения ключевой информации
- 🌐 **Graph-RAG**: Фильтрация по именованным сущностям
- 📊 **Готовые профили**: Шаблоны для различных задач (медицина, штрафы, детские сады)
- 🎨 **Современный UI**: Красивый веб-интерфейс на TailwindCSS
- ⚡ **Стрим-обработка**: Реальное время обновления прогресса

## 🎯 Поддерживаемые модели

- ✅ **Claude Opus 4.1** через VseGPT (текущая)
- ✅ **Qwen3 80B** через VseGPT  
- ✅ **GPT-4o-mini** через VseGPT/OpenAI
- ✅ **Локальные модели** через Ollama

## 🌐 Демо

**Попробуйте прямо сейчас:** https://vasilykolbenev.github.io/Multi_Agent_RAG_LE/

Система работает с Claude Opus 4.1 и готова к анализу ваших документов!

## 🚀 Развертывание

### ☁️ Облачное развертывание (рекомендуется)

**Railway (1 клик):**
1. Нажмите [![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template/multiagent-rag-pro)
2. Подключите GitHub репозиторий
3. Добавьте переменную `OPENAI_API_KEY`
4. Готово! 🎉

**Render:**
1. Форкните репозиторий
2. Создайте Web Service на [render.com](https://render.com)
3. Подключите GitHub репозиторий
4. Добавьте переменную окружения `OPENAI_API_KEY`

### 💻 Локальный запуск

```bash
# Клонируйте репозиторий
git clone https://github.com/your-username/multiagent-rag-pro
cd multiagent-rag-pro

# Установите зависимости
pip install -r requirements.txt

# Установите переменную окружения
export OPENAI_API_KEY="your_openai_key"

# Запуск
python run.py
```

### Способ 2: Ручная настройка
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Установите переменные окружения
export OPENAI_API_KEY="ваш_ключ_openai"
export LLM_PROVIDER="openai"
export LLM_MODEL="gpt-4o-mini"
export LX_MODEL_ID="openai:gpt-4o-mini"

uvicorn server.main:app --reload --port 8000
```

## Docker
```bash
docker build -t multiagent-rag-pro .
docker run -p 8000:8000 \
  -e OPENAI_API_KEY="ваш_ключ_openai" \
  -e LLM_PROVIDER="openai" \
  -e LLM_MODEL="gpt-4o-mini" \
  -e LX_MODEL_ID="openai:gpt-4o-mini" \
  multiagent-rag-pro
```

## GitHub Pages
Папка `docs/` готова к публикации. Открой:
https://<user>.github.io/<repo>/?api=https://<ваш-бэкенд-URL>
"# Force Vercel redeploy $(date)" 
"# Update $(date)" 
