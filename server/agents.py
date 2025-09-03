from typing import Dict, Any, List, Set, Optional
from .llm import LLM
from .retrieval import Corpus
from .graph_index import GraphIndex
from .langx import run_extraction

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

class MultiAgent:
    def __init__(self, corpus: Corpus, graph: GraphIndex):
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
