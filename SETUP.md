# 🚀 Настройка MultiAgent-RAG Pro

## Быстрый старт

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Настройка OpenAI API ключа

**Вариант A: Через переменные окружения (Рекомендуется)**
```bash
# Linux/Mac
export OPENAI_API_KEY="your-api-key-here"

# Windows PowerShell
$env:OPENAI_API_KEY = "your-api-key-here"
```

**Вариант B: Редактирование скрипта запуска**
1. Откройте `run.py` или `run.ps1`
2. Замените `YOUR_OPENAI_API_KEY_HERE` на ваш реальный ключ

### 3. Запуск приложения

**Python:**
```bash
python run.py
```

**PowerShell:**
```bash
./run.ps1
```

**Продакшн:**
```bash
python run_production.py
```

### 4. Доступ к приложению

- **Backend API:** http://localhost:8000
- **Frontend:** откройте `docs/index.html` в браузере
- **API Документация:** http://localhost:8000/docs

## Развертывание

### GitHub Pages (Frontend)
1. Включите GitHub Pages в настройках репозитория
2. Выберите папку `/docs` как источник
3. Frontend будет доступен по адресу: `https://username.github.io/repository-name`

### Railway/Render (Backend)
1. Подключите репозиторий к платформе
2. Добавьте переменную окружения `OPENAI_API_KEY`
3. Установите команду запуска: `python run_production.py`

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `OPENAI_API_KEY` | OpenAI API ключ | - |
| `LLM_PROVIDER` | Провайдер LLM | `openai` |
| `LLM_MODEL` | Модель LLM | `gpt-5-mini` |
| `LX_MODEL_ID` | Модель для извлечения | `openai:gpt-5-mini` |
| `DOCS_DIR` | Папка с документами | `data/docs` |
| `DATA_DIR` | Папка с данными | `data` |

## Безопасность

⚠️ **ВАЖНО:** Никогда не коммитьте файлы с реальными API ключами в Git!

✅ **Правильно:**
- Используйте переменные окружения
- Добавьте `.env` в `.gitignore`
- Используйте плейсхолдеры в коде

❌ **Неправильно:**
- Хранить ключи прямо в коде
- Коммитить `.env` файлы
- Публиковать ключи в репозитории
