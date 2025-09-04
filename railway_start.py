#!/usr/bin/env python3
"""
Упрощенный запуск для Railway с подробным логированием
"""
import uvicorn
import os

# Теперь вся логика конфигурации находится в server.config,
# который импортируется автоматически при запуске app.
# Этот файл остается максимально простым.

print("🚀 Railway Production Start Script")

try:
    # Просто импортируем, чтобы убедиться, что конфигурация загрузилась без ошибок
    from server import config
    
    port = int(os.environ.get("PORT", 8080))
    print(f"🌐 Starting server on port {port}...")

    uvicorn.run(
        "server.main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )

except Exception as e:
    print("❌ CRITICAL ERROR ON STARTUP ❌")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    # Выход с ошибкой, чтобы Railway показал статус "Crashed"
    exit(1)
