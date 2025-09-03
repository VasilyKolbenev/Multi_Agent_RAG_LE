#!/usr/bin/env python3
"""
Продакшн запуск MultiAgent-RAG Pro для облачного развертывания
"""
import os
import uvicorn
from pathlib import Path

# Создаем необходимые директории
Path("data/docs").mkdir(parents=True, exist_ok=True)
Path("data/extracts").mkdir(parents=True, exist_ok=True)

# Настройка переменных окружения с fallback значениями
def setup_environment():
    # Обязательные переменные
    required_vars = {
        "OPENAI_API_KEY": "Установите OPENAI_API_KEY в переменных окружения",
        "LLM_PROVIDER": "openai",
        "LLM_MODEL": "gpt-5-mini",
        "LX_MODEL_ID": "openai:gpt-5-mini"
    }
    
    # Опциональные переменные
    optional_vars = {
        "DOCS_DIR": "data/docs",
        "DATA_DIR": "data",
        "PORT": "8000"
    }
    
    # Проверяем обязательные переменные
    missing_vars = []
    for var, default in required_vars.items():
        if not os.environ.get(var):
            if var == "OPENAI_API_KEY":
                missing_vars.append(var)
            else:
                os.environ[var] = default
    
    # Устанавливаем опциональные переменные
    for var, default in optional_vars.items():
        if not os.environ.get(var):
            os.environ[var] = default
    
    # Выводим ошибки если есть
    if missing_vars:
        print("❌ Отсутствуют обязательные переменные окружения:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n📝 Установите переменные в вашей облачной платформе")
        return False
    
    return True

def main():
    print("🚀 MultiAgent-RAG Pro (Production Mode)")
    print("=" * 50)
    
    try:
        if not setup_environment():
            print("❌ Ошибка настройки окружения")
            exit(1)
        
        # Выводим конфигурацию
        print("📋 Конфигурация:")
        print(f"   LLM Provider: {os.environ.get('LLM_PROVIDER')}")
        print(f"   LLM Model: {os.environ.get('LLM_MODEL')}")
        print(f"   LangExtract Model: {os.environ.get('LX_MODEL_ID')}")
        print(f"   Port: {os.environ.get('PORT')}")
        print("   OpenAI API Key: ✅ Установлен")
        print()
        
        # Получаем порт (Railway устанавливает автоматически)
        port = int(os.environ.get("PORT", 8000))
        
        print(f"🌐 Запуск сервера на порту {port}")
        print("📖 После развертывания API будет доступно по адресу:")
        print("   https://your-app.railway.app/docs")
        
        # Запуск с продакшн настройками
        uvicorn.run(
            "server.main:app",
            host="0.0.0.0",
            port=port,
            reload=False,  # Отключаем reload в продакшн
            access_log=True,
            log_level="info"
        )
        
    except Exception as e:
        print(f"❌ Критическая ошибка при запуске: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()
