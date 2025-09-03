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
    if not docs:
        return []
    prompt = ("Отсортируй следующих кандидатов по релевантности к запросу. "
              "Верни только numerated list of indices, for example: 1. 3\n2. 1\n3. 0\n4. 2\n\n"
              f"Запрос: {query}\n\n" +
              "\n".join(f"[{i}] {d['text'][:700]}" for i, d in enumerate(docs)))
    
    try:
        response = await llm.complete("You are a helpful re-ranking assistant.", prompt)
        # Извлекаем числа из ответа
        ranked_indices = [int(i) for i in re.findall(r'\d+', response)]
        
        # Проверяем, что все индексы валидны
        if all(i < len(docs) for i in ranked_indices):
            # Создаем новый список на основе отсортированных индексов
            reranked_docs = [docs[i] for i in ranked_indices]
            # Добавляем оставшиеся документы, которых не было в ответе
            original_indices = set(range(len(docs)))
            used_indices = set(ranked_indices)
            remaining_indices = original_indices - used_indices
            for i in remaining_indices:
                reranked_docs.append(docs[i])
            return reranked_docs
        else:
            # Если LLM вернула невалидные индексы, возвращаем исходный порядок
            return docs
    except Exception:
        # В случае ошибки возвращаем исходный порядок
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
        
        # Шаг 1: Планирование (не потоковое)
        plan = await self.llm.complete(SYSTEM_PLANNER, query)
        yield {"type": "plan", "data": plan}
        
        # Шаг 2: Извлечение сущностей (не потоковое)
        extracted_entities = []
        if auto_extract and not entities_filter:
            try:
                extraction_result = run_extraction(query, "Извлеки людей, компании, места, события и даты из этого вопроса")
                extracted_entities = [item.get("text", "") for item in extraction_result.get("items", []) if item.get("text")]
                entities_filter = extracted_entities[:10]  # Ограничиваем до 10 сущностей
            except Exception as e:
                print(f"Ошибка извлечения сущностей: {e}")
        
        yield {"type": "entities", "data": extracted_entities}
        
        # Шаг 3: Гибридный поиск
        hits = self.corpus.search(query, k=k)
        yield {"type": "search_details", "data": {"search_type": "Hybrid (BM25 + Vector)", "candidates_found": len(hits)}}
        
        # Шаг 3.5: LLM Rerank
        reranked_hits = await llm_rerank(query, hits, self.llm)
        top_hits = reranked_hits[:5] # Берем топ-5 для контекста
        yield {"type": "rerank_details", "data": {"reranker_model": "gpt-5-mini", "final_context_chunks": len(top_hits)}}

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
        # Для этого нужно собрать полный ответ
        full_answer = "" # Это потребует изменений в логике, пока пропускаем
        # critique = await self.llm.complete(SYSTEM_CRITIC, f"Ответ: {full_answer}\n\nКонтекст: {ctx}")
        # yield {"type": "critique", "data": critique}
