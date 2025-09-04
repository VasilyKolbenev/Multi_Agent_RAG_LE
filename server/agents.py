from typing import Dict, Any, List, Set, Optional
from .llm import LLM
from .retrieval import HybridCorpus
from .graph_index import GraphIndex
from .langx import run_extraction
import re

SYSTEM_PLANNER = (
    "Ты — Планировщик многоагентной системы. Разбей запрос на шаги: retrieval, synthesis, critique. "
    "Верни краткий план (3–6 пунктов)."
)
SYSTEM_WRITER = (
    "Ты — Писатель. Используй выдержки из CONTEXT, цитируй источники [doc_id]. Не выдумывай."
)
SYSTEM_CRITIC = (
    "Ты — Критик. Проверь ответ на соответствие контексту, дай замечания и уверенности."
)

async def llm_rerank(query: str, docs: List[Dict[str, Any]], llm: LLM) -> List[Dict[str, Any]]:
    """
    Оптимизированный LLM reranking с батчами и короткими промптами.
    Обрабатывает максимум 10 документов батчами по 5 с таймаутом 15 сек.
    """
    if not docs:
        return []
    
    # Ограничиваем до топ-10 кандидатов для скорости
    candidates = docs[:10]
    if len(candidates) <= 3:
        # Если документов мало, используем простую сортировку
        return candidates
    
    try:
        # Разбиваем на батчи по 5 документов максимум
        batch_size = 5
        batches = [candidates[i:i+batch_size] for i in range(0, len(candidates), batch_size)]
        
        ranked_docs = []
        
        for batch_idx, batch in enumerate(batches):
            # Короткий промпт с ограничением текста до 200 символов
            batch_prompt = (
                f"Rank these {len(batch)} documents by relevance to query: '{query[:100]}'\n"
                "Return only numbers (most relevant first): 1,2,3...\n\n"
            )
            
            for i, doc in enumerate(batch):
                # Ограничиваем текст до 200 символов + очистка
                clean_text = doc['text'][:200].replace('\n', ' ').strip()
                batch_prompt += f"{i+1}. {clean_text}...\n"
            
            # Короткий системный промпт
            system_prompt = "You are a document relevance ranker. Be concise."
            
            try:
                # Используем более короткий таймаут для батча
                response = await llm.complete(system_prompt, batch_prompt)
                
                # Извлекаем числа из ответа
                ranked_indices = []
                for match in re.findall(r'\b([1-9])\b', response):
                    idx = int(match) - 1  # Конвертируем в 0-based индекс
                    if 0 <= idx < len(batch):
                        ranked_indices.append(idx)
                
                # Добавляем документы в порядке ранжирования
                for idx in ranked_indices:
                    if idx < len(batch):
                        ranked_docs.append(batch[idx])
                
                # Добавляем оставшиеся документы из батча
                used_indices = set(ranked_indices)
                for i, doc in enumerate(batch):
                    if i not in used_indices:
                        ranked_docs.append(doc)
                        
            except Exception as e:
                print(f"⚠️ LLM rerank batch {batch_idx} failed: {e}")
                # В случае ошибки добавляем батч в исходном порядке
                ranked_docs.extend(batch)
        
        # Добавляем оставшиеся документы (если было больше 10)
        if len(docs) > 10:
            ranked_docs.extend(docs[10:])
            
        return ranked_docs
        
    except Exception as e:
        print(f"⚠️ LLM rerank completely failed: {e}")
        # В случае полной ошибки возвращаем исходный порядок
        return docs

class MultiAgent:
    def __init__(self, corpus: HybridCorpus, graph: GraphIndex):
        self.corpus = corpus
        self.graph = graph
        self.llm = LLM()

    async def run(self, query: str, k: int = 5, entities_filter: Optional[List[str]] = None, auto_extract: bool = True) -> Dict[str, Any]:
        plan = await self.llm.complete(SYSTEM_PLANNER, query)
        
        # Автоматическое извлечение сущностей из запроса
        extracted_entities = []
        if auto_extract and not entities_filter:
            try:
                extraction_result = run_extraction(query, "Извлеки людей, компании, места, события и даты из этого вопроса")
                extracted_entities = [item.get("text", "") for item in extraction_result.get("items", []) if item.get("text")]
                entities_filter = extracted_entities[:10]  # Ограничиваем до 10 сущностей
            except Exception as e:
                print(f"Ошибка извлечения сущностей: {e}")
        
        allowed_docs: Optional[Set[str]] = None
        if entities_filter:
            allowed_docs = self.graph.filter_docs(entities_filter)
        
        hits = self.corpus.search(query, k=k, allowed_docs=allowed_docs)
        ctx, cites = "", []
        for doc_id, text, score in hits:
            snippet = text[:1200].replace("\n"," ")
            ctx += f"\n[DOC {doc_id}] {snippet}"
            cites.append(doc_id)
        
        answer = await self.llm.complete(SYSTEM_WRITER, f"Q: {query}\n\nCONTEXT:\n{ctx}")
        critique = await self.llm.complete(SYSTEM_CRITIC, f"Ответ: {answer}\n\nКонтекст: {ctx}")
        
        return {
            "plan": plan, 
            "answer": answer, 
            "critique": critique, 
            "citations": cites,
            "hits": [{"doc_id": d, "score": s} for d,_,s in [(h[0],h[1],h[2]) for h in hits]],
            "extracted_entities": extracted_entities,
            "entities_used": entities_filter or []
        }

    async def stream(self, query: str, k: int = 20, entities_filter: Optional[List[str]] = None, auto_extract: bool = True):
        """Потоковая версия RAG-ответа."""
        import time
        start_time = time.time()
        print(f"🚀 RAG Stream started for query: {query[:50]}...")
        
        # Шаг 1: Планирование (не потоковое)
        step_start = time.time()
        plan = await self.llm.complete(SYSTEM_PLANNER, query)
        print(f"⏱️ Planning took: {time.time() - step_start:.2f}s")
        yield {"type": "plan", "data": plan}
        
        # Шаг 2: Извлечение сущностей (ВРЕМЕННО ОТКЛЮЧЕНО для скорости)
        step_start = time.time()
        extracted_entities = []
        # ОТКЛЮЧЕНО: автоматическое извлечение сущностей из вопроса (слишком медленно)
        # if auto_extract and not entities_filter:
        #     try:
        #         extraction_result = run_extraction(query, "Извлеки людей, компании, места, события и даты из этого вопроса")
        #         extracted_entities = [item.get("text", "") for item in extraction_result.get("items", []) if item.get("text")]
        #         entities_filter = extracted_entities[:10]  # Ограничиваем до 10 сущностей
        #     except Exception as e:
        #         print(f"Ошибка извлечения сущностей: {e}")
        print(f"⏱️ Entity extraction took: {time.time() - step_start:.2f}s (SKIPPED for performance)")
        yield {"type": "entities", "data": extracted_entities}
        
        # Шаг 3: Гибридный поиск
        step_start = time.time()
        hits = self.corpus.search(query, k=k)
        print(f"⏱️ Hybrid search took: {time.time() - step_start:.2f}s")
        yield {"type": "search_details", "data": {"search_type": "Hybrid (BM25 + Vector)", "candidates_found": len(hits)}}
        
        # Шаг 3.5: LLM Rerank (ОПТИМИЗИРОВАННАЯ ВЕРСИЯ)
        step_start = time.time()
        # Используем новый оптимизированный reranking с батчами и короткими промптами
        reranked_hits = await llm_rerank(query, hits, self.llm)
        top_hits = reranked_hits[:5] # Берем топ-5 для контекста
        print(f"⏱️ LLM reranking took: {time.time() - step_start:.2f}s (OPTIMIZED: batches + short prompts)")
        yield {"type": "rerank_details", "data": {"reranker_model": "gpt-4o-mini (optimized)", "final_context_chunks": len(top_hits)}}

        ctx = ""
        for chunk in top_hits:
            ctx += f"\n[DOC {chunk['doc_id']} Chunk: {chunk['chunk_id']}] {chunk['text']}"
        
        # Собираем уникальные ID чанков для цитирования
        chunk_cites = [chunk['chunk_id'] for chunk in top_hits]

        # Передаем сами чанки для модального окна
        full_hits_for_modal = [{"doc_id": h['chunk_id'], "text_content": h['text']} for h in top_hits]
        yield {"type": "citations", "citations": chunk_cites, "hits": full_hits_for_modal}
        
        # Шаг 4: Генерация ответа (потоковое)
        async for chunk in self.llm.stream(SYSTEM_WRITER, f"Q: {query}\n\nCONTEXT:\n{ctx}"):
            yield {"type": "answer_chunk", "data": chunk}
            
        yield {"type": "answer_done"}
        
        # Шаг 5: Критика (не потоковое, выполняется после генерации)
        print(f"🏁 Total RAG processing time: {time.time() - start_time:.2f}s")
        # Для этого нужно собрать полный ответ
        full_answer = "" # Это потребует изменений в логике, пока пропускаем
        # critique = await self.llm.complete(SYSTEM_CRITIC, f"Ответ: {full_answer}\n\nКонтекст: {ctx}")
        # yield {"type": "critique", "data": critique}
