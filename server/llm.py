import os, json, httpx

class LLM:
    def __init__(self):
        self.provider = os.environ.get("LLM_PROVIDER", "openai").lower()
        self.model = os.environ.get("LLM_MODEL", "gpt-5-mini")
        self.key = os.environ.get("OPENAI_API_KEY")

    async def complete(self, system: str, user: str) -> str:
        if self.provider == "openai" and self.key:
            return await self._openai(system, user)
        if self.provider == "ollama":
            return await self._ollama(system, user)
        return self._stub(system, user)

    async def _openai(self, system: str, user: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [{"role":"system","content":system},{"role":"user","content":user}]
        }
        
        # Для модели gpt-5-mini используем только базовые параметры (temperature и max_tokens не поддерживаются)
        if not self.model.startswith("gpt-5"):
            payload["temperature"] = 0.2
            payload["max_tokens"] = 2000
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"].strip()

    async def _ollama(self, system: str, user: str) -> str:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post("http://localhost:11434/api/chat", json={
                "model": self.model,
                "messages": [{"role":"system","content":system},{"role":"user","content":user}],
                "options": {"temperature":0.2}
            })
            r.raise_for_status()
            txt = ""
            for line in r.text.splitlines():
                try:
                    obj = json.loads(line)
                    if "message" in obj and "content" in obj["message"]:
                        txt += obj["message"]["content"]
                except Exception:
                    pass
            return txt.strip() or "…"

    def _stub(self, system: str, user: str) -> str:
        # Более реалистичные заглушки в зависимости от системного промпта
        if "Планировщик" in system:
            return """План выполнения запроса:
1. Поиск релевантных документов в базе знаний
2. Анализ найденной информации
3. Синтез ответа на основе контекста
4. Проверка качества и релевантности ответа"""
        
        elif "Писатель" in system:
            return f"""На основе предоставленного контекста отвечаю на вопрос: "{user}"

Это демо-ответ системы MultiAgent-RAG Pro. В реальном режиме здесь будет развернутый ответ на основе найденных документов с цитированием источников [doc_1], [doc_2] и т.д.

Текущий запрос: {user[:100]}{'...' if len(user) > 100 else ''}

*Демо-режим: для получения реальных ответов настройте OpenAI API или локальную модель*"""
        
        elif "Критик" in system:
            return """Анализ ответа:
✅ Соответствие контексту: Хорошее
✅ Полнота ответа: Достаточная  
✅ Цитирование источников: Корректное
⚠️  Уверенность: Демо-режим (85%)

Рекомендации: Ответ соответствует заданному вопросу и основан на предоставленном контексте."""
        
        else:
            return f"""Демо-ответ на запрос: "{user[:100]}{'...' if len(user) > 100 else ''}"

Это имитация ответа LLM в демо-режиме. Система работает корректно, но для получения реальных ответов необходимо настроить:
- OpenAI API (для облачных моделей)
- Ollama (для локальных моделей)

Все остальные функции (поиск, индексация, API) работают в полном объеме."""
