#!/usr/bin/env python3
"""
Render.com entry point для MultiAgent RAG Pro
"""

import os
import sys
import uvicorn

# Добавляем корневую директорию в Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    # Render использует переменную PORT для определения порта
    port = int(os.environ.get("PORT", 8000))
    
    # Запускаем FastAPI приложение
    uvicorn.run(
        "server.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
