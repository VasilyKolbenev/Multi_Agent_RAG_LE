import os
import re
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
# Чистим ключ максимально агрессивно от скрытых символов
_raw_key = (os.getenv("OPENAI_API_KEY") or os.getenv("API _KEY") or os.getenv("API_KEY") or "")
_raw_key = _raw_key.strip().strip('"').strip("'")
# Удаляем все неразрешенные символы (оставляем только латиницу/цифры/-_.)
OPENAI_API_KEY = re.sub(r"[^A-Za-z0-9_\-.]", "", _raw_key)

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
else:
    # Project-scoped keys contain the project ID in the middle: sk-proj-<projid>-<rest>
    parts = OPENAI_API_KEY.split("-")
    if len(parts) >= 4 and parts[1] == "proj":
        inferred_project = parts[2]
        if OPENAI_PROJECT and OPENAI_PROJECT != inferred_project:
            print(
                "⚠️  OPENAI_PROJECT mismatch: env has"
                f" '{OPENAI_PROJECT}', but key implies '{inferred_project}'."
            )
        elif not OPENAI_PROJECT:
            print(
                "💡 Hint: Set OPENAI_PROJECT="
                f"{inferred_project} to match your project-scoped key."
            )
print(f"   - OPENAI_API_KEY length: {len(OPENAI_API_KEY)} (sanitized)")

# Загружаем дополнительные параметры OpenAI
OPENAI_PROJECT = os.getenv("OPENAI_PROJECT", "").strip()
OPENAI_ORGANIZATION = (
    os.getenv("OPENAI_ORG")
    or os.getenv("OPENAI_ORGANIZATION")
    or os.getenv("OPENAI_DEFAULT_ORG")
    or ""
).strip()

if OPENAI_API_KEY.startswith("sk-proj-") and not OPENAI_PROJECT:
    print(
        "⚠️  Detected project-scoped OpenAI key (sk-proj-...), "
        "but OPENAI_PROJECT variable is not set.\n"
        "   Set OPENAI_PROJECT to your project ID (found in the OpenAI dashboard) "
        "to avoid 401 errors."
    )

if OPENAI_PROJECT:
    print(f"   - OPENAI_PROJECT: {OPENAI_PROJECT}")
if OPENAI_ORGANIZATION:
    print(f"   - OPENAI_ORGANIZATION: {OPENAI_ORGANIZATION}")

# Остальные настройки
# Читаем модель из переменных окружения, по умолчанию gpt-5-mini
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5-mini").strip()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small").strip()
LX_MODEL_ID = os.getenv("LX_MODEL_ID", "gpt-4o-mini")  # Используем поддерживаемую LangExtract модель

print(f"   - LLM_MODEL: {LLM_MODEL}")
print(f"   - EMBEDDING_MODEL: {EMBEDDING_MODEL}")
