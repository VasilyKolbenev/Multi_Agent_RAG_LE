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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError(
        "CRITICAL: OPENAI_API_KEY is not set or could not be loaded. "
        "Please ensure it is in your .env file or Railway variables."
    )

# Печатаем маскированное значение для проверки в логах
print(f"   - OPENAI_API_KEY: Loaded (sk-proj-...{OPENAI_API_KEY[-4:]})")

# Остальные настройки
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
LX_MODEL_ID = os.getenv("LX_MODEL_ID", f"openai:{LLM_MODEL}")

print(f"   - LLM_MODEL: {LLM_MODEL}")
print(f"   - EMBEDDING_MODEL: {EMBEDDING_MODEL}")
