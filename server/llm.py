import os, json, httpx
import asyncio
from server import config

class LLM:
    def __init__(self, model=None, provider=None, key=None):
        self.model = model or config.LLM_MODEL
        self.provider = provider or os.environ.get("LLM_PROVIDER", "openai")
        self.key = key or config.OPENAI_API_KEY

    async def complete(self, system: str, user: str) -> str:
        if self.provider == "stub":
            return self._stub(system, user)
        elif self.provider == "openai":
            return await self._openai(system, user)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    async def stream(self, system: str, user: str):
        """Асинхронный генератор для потоковой передачи ответа."""
        if self.provider == "openai":
            async for chunk in self._openai_stream(system, user):
                yield chunk
        else:
            # Для других провайдеров (или stub) эмулируем поток
            full_response = await self.complete(system, user)
            for word in full_response.split():
                yield word + " "
                await asyncio.sleep(0.05)

    async def _openai(self, system: str, user: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        # Поддержка проектных/организационных ключей
        openai_project = os.getenv("OPENAI_PROJECT")
        openai_org = os.getenv("OPENAI_ORG") or os.getenv("OPENAI_ORGANIZATION")
        if openai_project:
            headers["OpenAI-Project"] = openai_project
        if openai_org:
            headers["OpenAI-Organization"] = openai_org
        payload = {
            "model": self.model,
            "messages": [{"role":"system","content":system},{"role":"user","content":user}]
        }
        
        # Для модели gpt-5-mini используем только базовые параметры (temperature и max_tokens не поддерживаются)
        if not self.model.startswith("gpt-5"):
            payload["temperature"] = 0.2
            payload["max_tokens"] = 2000
        async with httpx.AsyncClient(timeout=30) as client:  # Уменьшаем таймаут до 30 сек
            r = await client.post(url, headers=headers, json=payload)
            # Если ключ невалиден или отсутствует — мягкий фолбэк в stub
            if r.status_code == 401:
                print("[LLM] 401 Unauthorized from OpenAI. Falling back to stub provider.")
                return self._stub(system, user)
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"].strip()

    async def _openai_stream(self, system: str, user: str):
        """Асинхронный генератор для потоковой передачи от OpenAI."""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        openai_project = os.getenv("OPENAI_PROJECT")
        openai_org = os.getenv("OPENAI_ORG") or os.getenv("OPENAI_ORGANIZATION")
        if openai_project:
            headers["OpenAI-Project"] = openai_project
        if openai_org:
            headers["OpenAI-Organization"] = openai_org
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "stream": True,
        }
        if not self.model.startswith("gpt-5"):
            payload["temperature"] = 0.2
            payload["max_tokens"] = 2000

        async with httpx.AsyncClient(timeout=30) as client:  # Уменьшаем таймаут до 30 сек
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code == 401:
                    # В потоковом режиме вернём stub единым куском
                    yield self._stub(system, user)
                    return
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        data_str = line[len("data:"):].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            print(f"Failed to decode JSON: {data_str}")
                            continue

    async def _ollama(self, system: str, user: str) -> str:
        async with httpx.AsyncClient(timeout=30) as client:  # Уменьшаем таймаут до 30 сек
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
        # Улучшенный stub для более реалистичных ответов
        if "планировщик" in system.lower():
            return "1. Извлечь ключевые сущности из запроса.\n2. Найти релевантные документы.\n3. Синтезировать ответ на основе найденного.\n4. Проверить ответ на фактическую точность."
        
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
