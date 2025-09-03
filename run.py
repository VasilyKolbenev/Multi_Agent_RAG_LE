#!/usr/bin/env python3
"""
Скрипт запуска MultiAgent-RAG Pro с настроенными переменными окружения
"""
import os
import uvicorn

# Установка переменных окружения (только для локального тестирования)
# В продакшн используйте переменные окружения!
if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "YOUR_OPENAI_API_KEY_HERE"
os.environ["LLM_PROVIDER"] = "openai"
os.environ["LLM_MODEL"] = "gpt-5-mini"
os.environ["LX_MODEL_ID"] = "openai:gpt-5-mini"
os.environ["DOCS_DIR"] = "data/docs"
os.environ["DATA_DIR"] = "data"

if __name__ == "__main__":
    print("🚀 Запуск MultiAgent-RAG Pro")
    print("📋 Конфигурация:")
    print(f"   LLM Provider: {os.environ.get('LLM_PROVIDER')}")
    print(f"   LLM Model: {os.environ.get('LLM_MODEL')}")
    print(f"   LangExtract Model: {os.environ.get('LX_MODEL_ID')}")
    print(f"   OpenAI API Key: {'✅ Установлен' if os.environ.get('OPENAI_API_KEY') else '❌ Не найден'}")
    print("🌐 Сервер будет доступен по адресу: http://localhost:8000")
    print("📖 Документация API: http://localhost:8000/docs")
    
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=True)
