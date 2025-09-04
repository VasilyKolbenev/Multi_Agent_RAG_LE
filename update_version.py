#!/usr/bin/env python3
"""
Скрипт для автоматического обновления версии фронтенда.
Запускается перед каждым git push для обеспечения видимости изменений.
"""

import re
import datetime
from pathlib import Path

def update_frontend_version():
    """Обновляет версию и timestamp в index.html"""
    
    index_path = Path("docs/index.html")
    if not index_path.exists():
        print("❌ Файл docs/index.html не найден!")
        return False
    
    # Читаем содержимое
    content = index_path.read_text(encoding='utf-8')
    
    # Текущие дата и время
    now = datetime.datetime.now()
    version_date = now.strftime("%Y-%m-%d %H:%M")
    build_date = now.strftime("%Y%m%d")
    
    # Увеличиваем версию (извлекаем текущую и увеличиваем)
    version_match = re.search(r'v(\d+)\.(\d+)', content)
    if version_match:
        major, minor = map(int, version_match.groups())
        minor += 1
        new_version = f"v{major}.{minor}"
    else:
        new_version = "v2.2"
    
    # Обновляем title
    content = re.sub(
        r'<title>.*?</title>',
        f'<title>MultiAgent‑RAG Pro {new_version} - Auto Updated!</title>',
        content
    )
    
    # Обновляем версию в header
    content = re.sub(
        r'✅ v[\d.]+ - .*? \| 🕐 Обновлено: [\d\-: ]+',
        f'✅ {new_version} - Auto Updated! | 🕐 Обновлено: {version_date}',
        content
    )
    
    # Обновляем build info
    content = re.sub(
        r'Build: [\w\-]+',
        f'Build: AUTO-UPDATE-{build_date}',
        content
    )
    
    # Обновляем cache buster
    content = re.sub(
        r"const CACHE_BUSTER = '.*?';",
        f"const CACHE_BUSTER = '?v={new_version}-auto-{now.timestamp():.0f}';",
        content
    )
    
    # Сохраняем
    index_path.write_text(content, encoding='utf-8')
    
    print(f"✅ Версия обновлена до {new_version}")
    print(f"📅 Дата: {version_date}")
    print(f"🏗️ Build: AUTO-UPDATE-{build_date}")
    
    return True

if __name__ == "__main__":
    print("🔄 Обновление версии фронтенда...")
    if update_frontend_version():
        print("🎉 Готово! Фронтенд обновлен.")
    else:
        print("❌ Ошибка при обновлении.")
