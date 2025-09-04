#!/usr/bin/env python3
"""
Скрипт для удобного деплоя с автоматическим обновлением версии.
Использование: python deploy.py "Описание изменений"
"""

import sys
import subprocess
from pathlib import Path
from update_version import update_frontend_version

def run_command(cmd, description):
    """Выполняет команду и показывает результат"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - OK")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - ОШИБКА:")
        print(f"   {e.stderr}")
        return False

def deploy_with_version_update(commit_message):
    """Полный цикл деплоя с обновлением версии"""
    
    print("🚀 Начинаем деплой MultiAgent-RAG Pro...")
    print("=" * 50)
    
    # 1. Обновляем версию фронтенда
    print("1️⃣ Обновление версии фронтенда...")
    if not update_frontend_version():
        print("❌ Не удалось обновить версию!")
        return False
    
    # 2. Добавляем все файлы в git
    if not run_command("git add .", "Добавление файлов в git"):
        return False
    
    # 3. Проверяем статус
    print("\n📋 Статус git:")
    subprocess.run("git status --short", shell=True)
    
    # 4. Коммитим изменения
    commit_cmd = f'git commit -m "{commit_message}"'
    if not run_command(commit_cmd, "Создание коммита"):
        return False
    
    # 5. Пушим на GitHub
    if not run_command("git push origin main", "Отправка на GitHub"):
        return False
    
    print("\n🎉 ДЕПЛОЙ ЗАВЕРШЕН УСПЕШНО!")
    print("📱 Frontend: https://vasilykolbenev.github.io/multiagent-rag-pro/")
    print("🖥️ Backend: https://multiagentragle-production.up.railway.app")
    print("📊 Архитектура: architecture_diagrams.html")
    print("\n💡 Обновите страницу (Ctrl+F5) чтобы увидеть изменения!")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Укажите описание изменений!")
        print("Использование: python deploy.py \"Описание изменений\"")
        print("Пример: python deploy.py \"Исправлен LangExtract API key\"")
        sys.exit(1)
    
    commit_message = sys.argv[1]
    deploy_with_version_update(commit_message)
