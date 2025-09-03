# Техническая документация MultiAgent-RAG Pro

## Архитектура системы

MultiAgent-RAG Pro состоит из следующих компонентов:

### Агенты
1. **Планировщик** - анализирует запрос и составляет план
2. **Писатель** - генерирует ответ на основе найденных документов  
3. **Критик** - проверяет качество ответа

### Технологии
- **Backend**: Python, FastAPI, uvicorn
- **LLM**: OpenAI GPT-5-mini
- **Search**: BM25 (rank-bm25)
- **Entity Extraction**: LangExtract
- **Frontend**: HTML, JavaScript, TailwindCSS

### API Endpoints

- `GET /health` - проверка состояния
- `GET /ask` - многоагентный запрос
- `GET /search` - поиск документов
- `POST /ingest/text` - добавление текста
- `POST /langextract/text` - извлечение сущностей

## Конфигурация

Переменные окружения:
- `OPENAI_API_KEY` - ключ OpenAI API
- `LLM_MODEL` - модель (gpt-5-mini)
- `LLM_PROVIDER` - провайдер (openai)

## Установка

```bash
pip install -r requirements.txt
python run.py
```

Версия: 1.0.0
Автор: MultiAgent Team
Лицензия: MIT
