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

# Определяем провайдера
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").strip().lower()


def _pick_env(*names: str) -> str:
    for name in names:
        value = os.getenv(name)
        if value and value.strip():
            return value
    return ""

# Универсальный ключ (поддерживаем OpenAI, VseGPT и другие OpenAI-совместимые API)
_raw_key = _pick_env("LLM_API_KEY", "OPENAI_API_KEY", "API_KEY", "API _KEY")
_raw_key = _raw_key.strip().strip('"').strip("'") if _raw_key else ""
LLM_API_KEY = re.sub(r"[^A-Za-z0-9_\-.]", "", _raw_key)
OPENAI_API_KEY = LLM_API_KEY

if not LLM_API_KEY:
    if LLM_PROVIDER not in {"stub", ""}:
        print(
            "⚠️  API key not provided; falling back to stub provider."
        )
    LLM_PROVIDER = "stub"

# Совместимость со старым именем

if LLM_API_KEY:
    print(f"   - LLM_API_KEY: Loaded (***{LLM_API_KEY[-4:]})")
else:
    print("   - LLM_API_KEY: not provided (stub provider)")

# Дополнительные настройки для OpenAI
OPENAI_PROJECT = ""
OPENAI_ORGANIZATION = ""
if LLM_PROVIDER == "openai":
    OPENAI_PROJECT = os.getenv("OPENAI_PROJECT", "").strip()
    OPENAI_ORGANIZATION = (
        os.getenv("OPENAI_ORG")
        or os.getenv("OPENAI_ORGANIZATION")
        or os.getenv("OPENAI_DEFAULT_ORG")
        or ""
    ).strip()

    if LLM_API_KEY.startswith("sk-proj-") and not OPENAI_PROJECT:
        print(
            "⚠️  Detected project-scoped OpenAI key (sk-proj-...), but OPENAI_PROJECT variable is not set."
        )
    if OPENAI_PROJECT:
        print(f"   - OPENAI_PROJECT: {OPENAI_PROJECT}")
    if OPENAI_ORGANIZATION:
        print(f"   - OPENAI_ORGANIZATION: {OPENAI_ORGANIZATION}")

# Базовый URL (в том числе для VseGPT)
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "").strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
OPENAI_EMBED_BASE_URL = os.getenv("OPENAI_EMBED_BASE_URL", "").strip()
VSEGPT_BASE_URL = (
    os.getenv("VSEGPT_BASE_URL")
    or os.getenv("VSE_GPT_BASE_URL")
    or "https://api.vsegpt.ru/v1"
).strip()

# Остальные настройки
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small").strip()
LX_MODEL_ID = os.getenv("LX_MODEL_ID", "gpt-4o-mini")

print(f"   - LLM_PROVIDER: {LLM_PROVIDER}")
print(f"   - LLM_MODEL: {LLM_MODEL}")
print(f"   - EMBEDDING_MODEL: {EMBEDDING_MODEL}")
print(f"   - VSEGPT_BASE_URL: {VSEGPT_BASE_URL}")
