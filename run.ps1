# Скрипт запуска MultiAgent-RAG Pro для PowerShell
Write-Host "🚀 Запуск MultiAgent-RAG Pro" -ForegroundColor Green

# Установка переменных окружения
$env:OPENAI_API_KEY = "YOUR_OPENAI_API_KEY_HERE"
$env:LLM_PROVIDER = "openai"
$env:LLM_MODEL = "gpt-5-mini"
$env:LX_MODEL_ID = "openai:gpt-5-mini"
$env:DOCS_DIR = "data/docs"
$env:DATA_DIR = "data"

Write-Host "📋 Конфигурация:" -ForegroundColor Yellow
Write-Host "   LLM Provider: $($env:LLM_PROVIDER)"
Write-Host "   LLM Model: $($env:LLM_MODEL)"
Write-Host "   LangExtract Model: $($env:LX_MODEL_ID)"
if ($env:OPENAI_API_KEY) {
    Write-Host "   OpenAI API Key: ✅ Установлен" -ForegroundColor Green
} else {
    Write-Host "   OpenAI API Key: ❌ Не найден" -ForegroundColor Red
}
Write-Host "🌐 Сервер будет доступен по адресу: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📖 Документация API: http://localhost:8000/docs" -ForegroundColor Cyan

# Запуск сервера
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
