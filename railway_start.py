#!/usr/bin/env python3
"""
Упрощенный запуск для Railway с подробным логированием
"""
import os
import sys
from pathlib import Path

print("🔍 Railway Debug Start")
print("=" * 50)

# Создаем директории
print("📁 Создание директорий...")
try:
    Path("data/docs").mkdir(parents=True, exist_ok=True)
    Path("data/extracts").mkdir(parents=True, exist_ok=True)
    print("✅ Директории созданы")
except Exception as e:
    print(f"❌ Ошибка создания директорий: {e}")

# Проверяем переменные окружения
print("\n🔧 Проверка переменных окружения...")
required_vars = ["OPENAI_API_KEY", "LLM_PROVIDER", "LLM_MODEL", "LX_MODEL_ID"]
for var in required_vars:
    value = os.environ.get(var)
    if value:
        print(f"✅ {var}: {'*' * 10}")
    else:
        print(f"❌ {var}: не установлена")

# Устанавливаем defaults
os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("LLM_MODEL", "gpt-5-mini") 
os.environ.setdefault("LX_MODEL_ID", "openai:gpt-5-mini")
os.environ.setdefault("DOCS_DIR", "data/docs")
os.environ.setdefault("DATA_DIR", "data")

print("\n📦 Проверка импортов...")
try:
    import uvicorn
    print("✅ uvicorn")
    
    import fastapi
    print("✅ fastapi")
    
    # Проверяем наши модули
    sys.path.insert(0, '.')
    from server.main import app
    print("✅ server.main")
    
except Exception as e:
    print(f"❌ Ошибка импорта: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n🚀 Запуск сервера...")
port = int(os.environ.get("PORT", 8000))
print(f"🌐 Порт: {port}")

try:
    uvicorn.run(
        "server.main:app",
        host="0.0.0.0", 
        port=port,
        reload=False,
        log_level="debug"
    )
except Exception as e:
    print(f"❌ Ошибка запуска: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
