#!/usr/bin/env python3
"""
Публичный запуск MultiAgent-RAG Pro для доступа из интернета
"""
import os
import uvicorn
import socket

# Установка переменных окружения
os.environ["OPENAI_API_KEY"] = "YOUR_OPENAI_API_KEY_HERE"
os.environ["LLM_PROVIDER"] = "openai"
os.environ["LLM_MODEL"] = "gpt-5-mini"
os.environ["LX_MODEL_ID"] = "openai:gpt-5-mini"
os.environ["DOCS_DIR"] = "data/docs"
os.environ["DATA_DIR"] = "data"

def get_local_ip():
    """Получает локальный IP адрес"""
    try:
        # Создаем временное соединение для определения IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

if __name__ == "__main__":
    local_ip = get_local_ip()
    
    print("🌐 Запуск MultiAgent-RAG Pro (Публичный режим)")
    print("📋 Конфигурация:")
    print(f"   LLM Provider: {os.environ.get('LLM_PROVIDER')}")
    print(f"   LLM Model: {os.environ.get('LLM_MODEL')}")
    print(f"   LangExtract Model: {os.environ.get('LX_MODEL_ID')}")
    print("   OpenAI API Key: ✅ Установлен")
    print()
    print("🔗 Доступ к серверу:")
    print(f"   Локально: http://localhost:8000")
    print(f"   В локальной сети: http://{local_ip}:8000")
    print(f"   Документация API: http://{local_ip}:8000/docs")
    print()
    print("⚠️  Внимание:")
    print("   - Сервер доступен всем в вашей сети")
    print("   - Для интернет-доступа нужно настроить роутер")
    print("   - Или используйте ngrok/cloudflare tunnel")
    print()
    
    # Запуск на всех интерфейсах
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=False)
