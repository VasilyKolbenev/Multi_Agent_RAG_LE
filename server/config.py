import os
from dotenv import load_dotenv
from pathlib import Path

# --- Централизованная загрузка конфигурации ---

# Явно указываем путь к .env файлу в корне проекта
# Это самый надежный способ для Railway
env_path = Path(__file__).parent.parent / '.env'

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"✅ Config: Loaded environment variables from {env_path.resolve()}")
else:
    print(f"⚠️ Config: .env file at {env_path.resolve()} not found. Relying on system environment variables.")

# --- Главные переменные конфигурации ---

# Загружаем ключ OpenAI и сразу проверяем его наличие
# Сначала пробуем системные переменные (Railway UI Variables)
# Подтягиваем ключ и убираем случайные пробелы/переносы строк/кавычки
OPENAI_API_KEY = (os.getenv("OPENAI_API_KEY") or os.getenv("API _KEY") or os.getenv("API_KEY") or "").strip().strip('"').strip("'")

# Если не нашли, показываем подробную диагностику
if not OPENAI_API_KEY:
    print("🔍 OPENAI_API_KEY not found. Debugging...")
    print(f"   - Environment variables count: {len(os.environ)}")
    
    # Ищем переменные, которые могут содержать ключ
    api_key_vars = [k for k in os.environ.keys() if 'API' in k.upper() or 'KEY' in k.upper()]
    if api_key_vars:
        print(f"   - Found API/KEY variables: {api_key_vars}")
        for var in api_key_vars:
            value = os.environ[var]
            print(f"     * {var}: {value[:10]}...{value[-4:] if len(value) > 14 else value}")
    else:
        print("   - No API/KEY variables found in environment")
    
    raise ValueError(
        "CRITICAL: OPENAI_API_KEY is not set or could not be loaded. "
        "Please ensure it is set as 'OPENAI_API_KEY' in Railway Variables."
    )

# Печатаем маскированное значение для проверки в логах
print(f"   - OPENAI_API_KEY: Loaded (sk-proj-...{OPENAI_API_KEY[-4:]})")
if not OPENAI_API_KEY.startswith("sk-"):
    print("⚠️  OPENAI_API_KEY doesn't start with 'sk-'. Check for extra characters or wrong key type.")

# Остальные настройки
# Читаем модель из переменных окружения, по умолчанию gpt-5-mini
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5-mini").strip()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small").strip()
LX_MODEL_ID = os.getenv("LX_MODEL_ID", "gpt-4o-mini")  # Используем поддерживаемую LangExtract модель

print(f"   - LLM_MODEL: {LLM_MODEL}")
print(f"   - EMBEDDING_MODEL: {EMBEDDING_MODEL}")
