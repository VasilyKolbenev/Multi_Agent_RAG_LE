# 🚀 Развертывание на Vercel

## Пошаговая инструкция

### 1. Подготовка
Коммитим и пушим изменения:
```bash
git add .
git commit -m "Add Vercel deployment configuration"
git push
```

### 2. Создание проекта на Vercel

1. Перейдите на [vercel.com](https://vercel.com)
2. Войдите через GitHub аккаунт
3. Нажмите **"New Project"**
4. Выберите репозиторий **"Multi_Agent_RAG_LE"**
5. Нажмите **"Import"**

### 3. Настройки проекта

**Framework Preset**: Other
**Root Directory**: `.` (корень)
**Build Command**: (оставить пустым)
**Output Directory**: (оставить пустым)

### 4. Переменные окружения

В разделе **Environment Variables** добавьте:
```
OPENAI_API_KEY=sk-proj-ваш-ключ-здесь
LLM_MODEL=gpt-5-mini
EMBEDDING_MODEL=text-embedding-3-small
```

### 5. Развертывание

1. Нажмите **"Deploy"**
2. Vercel автоматически развернет проект
3. Получите URL вида: `https://your-project.vercel.app`

### 6. Проверка

Откройте: `https://your-project.vercel.app/health`

Должны увидеть:
```json
{"ok": true, "model": "gpt-5-mini"}
```

## 📁 Структура для Vercel

```
/
├── api/
│   ├── vercel_main.py    # Главный API файл
│   └── requirements.txt  # Зависимости Python
├── vercel.json          # Конфигурация Vercel
└── react-ui/           # Frontend (деплоится отдельно)
```

## 🎯 Особенности Vercel версии

### ✅ Что работает:
- Загрузка документов (в памяти)
- Простой поиск по документам
- Базовые API endpoints
- CORS настройки
- Переменные окружения

### ⚠️ Упрощения:
- Хранилище в памяти (не персистентное)
- Упрощенный поиск (без векторных эмбеддингов)
- Базовые ответы (без полной OpenAI интеграции)
- Без LangExtract функций

### 🔧 Для полной функциональности:
Добавьте в `api/requirements.txt`:
```
openai==1.3.5
numpy==1.24.3
sentence-transformers==2.2.2
```

И обновите `api/vercel_main.py` с полной логикой из `server/main.py`.

## 🚀 Преимущества Vercel

- ✅ **Полностью бесплатный** (без карты)
- ✅ **Автодеплой** из GitHub
- ✅ **Serverless** архитектура
- ✅ **HTTPS** из коробки
- ✅ **Быстрый** холодный старт
- ✅ **Простая настройка**

## 🔄 Workflow

1. Разработка → локально
2. Коммит → в GitHub  
3. Автодеплой → на Vercel
4. Тестирование → на продакшн URL

## 📋 Troubleshooting

### Превышение лимитов
Vercel имеет лимиты на:
- Размер функции: 50MB
- Время выполнения: 30 секунд
- Память: 1024MB

### Решение:
- Используйте упрощенную версию API
- Уберите тяжелые зависимости
- Оптимизируйте импорты

Готово! Ваш API теперь на Vercel 🎉
