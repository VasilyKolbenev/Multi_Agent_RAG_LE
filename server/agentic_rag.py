"""
🚀 Agentic RAG System - Умная многоагентная система поиска и генерации

Основано на статье: https://habr.com/ru/articles/942278/
Архитектура: Router Agent → Retrieval Agents → Query Rewriter → Synthesis Agent
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from .llm import LLM
from .retrieval import HybridCorpus
from .graph_index import GraphIndex
from .langx import run_extraction


class SearchStrategy(Enum):
    """Стратегии поиска для агентов"""
    VECTOR_SEARCH = "vector"
    BM25_SEARCH = "bm25" 
    HYBRID_SEARCH = "hybrid"
    ENTITY_EXTRACTION = "entities"
    EXTERNAL_API = "external"


class AgentDecision(Enum):
    """Решения агентов"""
    CONTINUE = "continue"
    REWRITE_QUERY = "rewrite"
    CHANGE_STRATEGY = "change_strategy"
    SUFFICIENT = "sufficient"
    FAILED = "failed"


@dataclass
class SearchResult:
    """Результат поиска с метаданными"""
    content: List[Dict[str, Any]]
    strategy: SearchStrategy
    relevance_score: float
    confidence: float
    metadata: Dict[str, Any]


@dataclass
class AgentState:
    """Состояние агентной системы"""
    original_query: str
    current_query: str
    iteration: int
    strategies_tried: List[SearchStrategy]
    results_history: List[SearchResult]
    accumulated_context: str
    confidence_threshold: float = 0.7
    max_iterations: int = 5


class RouterAgent:
    """🎯 Агент-маршрутизатор: выбирает стратегию поиска"""
    
    def __init__(self, llm: LLM):
        self.llm = llm
        
    async def analyze_query(self, query: str, state: AgentState) -> SearchStrategy:
        """Анализирует запрос и выбирает оптимальную стратегию поиска"""
        
        analysis_prompt = f"""
        Проанализируй запрос пользователя и выбери лучшую стратегию поиска:
        
        ЗАПРОС: "{query}"
        ИТЕРАЦИЯ: {state.iteration}
        УЖЕ ПРОБОВАЛИ: {[s.value for s in state.strategies_tried]}
        
        ДОСТУПНЫЕ СТРАТЕГИИ:
        1. HYBRID - гибридный поиск (BM25 + векторы) - универсальный
        2. ENTITIES - извлечение сущностей через LangExtract - для вопросов о людях, компаниях, датах
        3. VECTOR - только семантический поиск - для концептуальных вопросов
        4. BM25 - только ключевые слова - для точных терминов
        
        ПРАВИЛА:
        - Если запрос содержит имена, компании, даты → ENTITIES
        - Если запрос концептуальный, абстрактный → VECTOR  
        - Если запрос с точными терминами → BM25
        - По умолчанию → HYBRID
        - Не повторяй уже испробованные стратегии
        
        Ответь ТОЛЬКО названием стратегии: HYBRID/ENTITIES/VECTOR/BM25
        """
        
        try:
            response = await self.llm.complete(
                "Ты - эксперт по выбору стратегий поиска. Будь лаконичен.",
                analysis_prompt
            )
            
            # Парсим ответ
            strategy_map = {
                "HYBRID": SearchStrategy.HYBRID_SEARCH,
                "ENTITIES": SearchStrategy.ENTITY_EXTRACTION, 
                "VECTOR": SearchStrategy.VECTOR_SEARCH,
                "BM25": SearchStrategy.BM25_SEARCH
            }
            
            for key, strategy in strategy_map.items():
                if key in response.upper():
                    if strategy not in state.strategies_tried:
                        return strategy
            
            # Fallback: выбираем первую неиспробованную
            available = [s for s in SearchStrategy if s not in state.strategies_tried]
            return available[0] if available else SearchStrategy.HYBRID_SEARCH
            
        except Exception as e:
            print(f"⚠️ Router Agent error: {e}")
            return SearchStrategy.HYBRID_SEARCH


class RetrievalAgent:
    """🔍 Агент выборки: выполняет поиск по выбранной стратегии"""
    
    def __init__(self, corpus: HybridCorpus, graph: GraphIndex):
        self.corpus = corpus
        self.graph = graph
        
    async def execute_search(self, query: str, strategy: SearchStrategy, k: int = 10) -> SearchResult:
        """Выполняет поиск по указанной стратегии"""
        
        start_time = time.time()
        
        try:
            if strategy == SearchStrategy.HYBRID_SEARCH:
                results = self.corpus.search(query, k=k)
                content = [{"text": r["text"], "doc_id": r["doc_id"], "chunk_id": r["chunk_id"]} for r in results]
                
            elif strategy == SearchStrategy.ENTITY_EXTRACTION:
                # Извлекаем сущности из запроса
                extraction = run_extraction(query, "Извлеки все упомянутые сущности: людей, компании, места, даты")
                entities = [item.get("text", "") for item in extraction.get("items", [])]
                
                # Ищем документы с этими сущностями
                if entities:
                    allowed_docs = self.graph.filter_docs(entities[:10])
                    results = self.corpus.search(query, k=k)  # TODO: добавить фильтрацию по allowed_docs
                    content = [{"text": r["text"], "doc_id": r["doc_id"], "entities": entities} for r in results]
                else:
                    # Fallback на гибридный поиск
                    results = self.corpus.search(query, k=k)
                    content = [{"text": r["text"], "doc_id": r["doc_id"]} for r in results]
                    
            elif strategy == SearchStrategy.VECTOR_SEARCH:
                # TODO: Реализовать чистый векторный поиск
                results = self.corpus.search(query, k=k)
                content = [{"text": r["text"], "doc_id": r["doc_id"], "search_type": "vector"} for r in results]
                
            elif strategy == SearchStrategy.BM25_SEARCH:
                # TODO: Реализовать чистый BM25 поиск
                results = self.corpus.search(query, k=k)
                content = [{"text": r["text"], "doc_id": r["doc_id"], "search_type": "bm25"} for r in results]
                
            else:
                content = []
                
            # Вычисляем метрики
            relevance_score = self._calculate_relevance(query, content)
            confidence = self._calculate_confidence(content, strategy)
            
            search_time = time.time() - start_time
            
            return SearchResult(
                content=content,
                strategy=strategy,
                relevance_score=relevance_score,
                confidence=confidence,
                metadata={
                    "search_time": search_time,
                    "results_count": len(content),
                    "query_length": len(query)
                }
            )
            
        except Exception as e:
            print(f"⚠️ Retrieval Agent error with {strategy.value}: {e}")
            return SearchResult(
                content=[],
                strategy=strategy,
                relevance_score=0.0,
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    def _calculate_relevance(self, query: str, content: List[Dict]) -> float:
        """Простая оценка релевантности на основе пересечения слов"""
        if not content:
            return 0.0
            
        query_words = set(query.lower().split())
        total_overlap = 0
        
        for item in content:
            text_words = set(item.get("text", "").lower().split())
            overlap = len(query_words & text_words)
            total_overlap += overlap
            
        # Нормализуем по количеству результатов и слов в запросе
        max_possible = len(query_words) * len(content)
        return min(total_overlap / max(max_possible, 1), 1.0)
    
    def _calculate_confidence(self, content: List[Dict], strategy: SearchStrategy) -> float:
        """Оценка уверенности в результатах"""
        if not content:
            return 0.0
            
        # Базовая уверенность зависит от стратегии
        base_confidence = {
            SearchStrategy.HYBRID_SEARCH: 0.8,
            SearchStrategy.ENTITY_EXTRACTION: 0.9,
            SearchStrategy.VECTOR_SEARCH: 0.7,
            SearchStrategy.BM25_SEARCH: 0.6
        }.get(strategy, 0.5)
        
        # Корректируем по количеству результатов
        count_factor = min(len(content) / 5, 1.0)  # Оптимально 5+ результатов
        
        return base_confidence * count_factor


class QueryRewriterAgent:
    """✏️ Агент переписывания запросов: улучшает запрос для лучшего поиска"""
    
    def __init__(self, llm: LLM):
        self.llm = llm
        
    async def rewrite_query(self, state: AgentState, last_result: SearchResult) -> str:
        """Переписывает запрос на основе предыдущих результатов"""
        
        rewrite_prompt = f"""
        ЗАДАЧА: Улучши запрос для лучшего поиска документов.
        
        ИСХОДНЫЙ ЗАПРОС: "{state.original_query}"
        ТЕКУЩИЙ ЗАПРОС: "{state.current_query}"
        ИТЕРАЦИЯ: {state.iteration}
        
        ПОСЛЕДНИЙ РЕЗУЛЬТАТ:
        - Стратегия: {last_result.strategy.value}
        - Релевантность: {last_result.relevance_score:.2f}
        - Уверенность: {last_result.confidence:.2f}
        - Найдено результатов: {len(last_result.content)}
        
        ПРОБЛЕМЫ:
        {"- Низкая релевантность" if last_result.relevance_score < 0.3 else ""}
        {"- Мало результатов" if len(last_result.content) < 3 else ""}
        {"- Низкая уверенность" if last_result.confidence < 0.5 else ""}
        
        ПРАВИЛА ПЕРЕПИСЫВАНИЯ:
        1. Если мало результатов → добавь синонимы и альтернативные формулировки
        2. Если низкая релевантность → уточни ключевые термины
        3. Если низкая уверенность → упрости запрос, убери лишние детали
        4. Сохрани основной смысл исходного запроса
        5. Используй русский язык
        
        Верни ТОЛЬКО переписанный запрос, без объяснений.
        """
        
        try:
            rewritten = await self.llm.complete(
                "Ты - эксперт по переформулированию поисковых запросов.",
                rewrite_prompt
            )
            
            # Очищаем ответ
            rewritten = rewritten.strip().strip('"').strip("'")
            
            # Проверяем, что запрос действительно изменился
            if rewritten.lower() == state.current_query.lower():
                # Если LLM вернула тот же запрос, добавляем синонимы
                fallback_query = f"{state.original_query} синонимы альтернативы"
                print(f"⚠️ Query rewriter returned same query, using fallback")
                return fallback_query
                
            return rewritten
            
        except Exception as e:
            print(f"⚠️ Query Rewriter error: {e}")
            # Fallback: добавляем "подробно" к исходному запросу
            return f"{state.original_query} подробно"


class EvaluationAgent:
    """📊 Агент оценки: определяет качество результатов и следующие шаги"""
    
    def __init__(self, llm: LLM):
        self.llm = llm
        
    async def evaluate_results(self, state: AgentState, result: SearchResult) -> Tuple[AgentDecision, str]:
        """Оценивает результаты и принимает решение о дальнейших действиях"""
        
        # Быстрая оценка по метрикам
        if result.confidence >= state.confidence_threshold and result.relevance_score >= 0.5:
            if len(result.content) >= 3:
                return AgentDecision.SUFFICIENT, "Найдено достаточно релевантной информации"
        
        # Если итераций слишком много
        if state.iteration >= state.max_iterations:
            return AgentDecision.SUFFICIENT, "Достигнуто максимальное количество итераций"
        
        # Если все стратегии испробованы
        available_strategies = [s for s in SearchStrategy if s not in state.strategies_tried]
        if not available_strategies:
            return AgentDecision.SUFFICIENT, "Все стратегии поиска испробованы"
        
        # Решение на основе качества результатов
        if len(result.content) == 0:
            return AgentDecision.CHANGE_STRATEGY, "Нет результатов, меняем стратегию"
        elif result.relevance_score < 0.3:
            return AgentDecision.REWRITE_QUERY, "Низкая релевантность, переписываем запрос"
        elif result.confidence < 0.4:
            return AgentDecision.CHANGE_STRATEGY, "Низкая уверенность, меняем стратегию"
        else:
            return AgentDecision.CONTINUE, "Результаты удовлетворительные, продолжаем поиск"


class SynthesisAgent:
    """🔄 Агент синтеза: объединяет результаты и генерирует финальный ответ"""
    
    def __init__(self, llm: LLM):
        self.llm = llm
        
    async def synthesize_response(self, state: AgentState) -> Dict[str, Any]:
        """Синтезирует финальный ответ из всех собранных результатов"""
        
        # Собираем все уникальные результаты
        all_content = []
        all_sources = set()
        
        for result in state.results_history:
            for item in result.content:
                source_id = item.get("doc_id", "") + item.get("chunk_id", "")
                if source_id not in all_sources:
                    all_content.append(item)
                    all_sources.add(source_id)
        
        # Ограничиваем контекст для LLM
        top_content = all_content[:10]
        
        # Формируем контекст
        context = ""
        citations = []
        
        for i, item in enumerate(top_content):
            doc_id = item.get("doc_id", f"doc_{i}")
            chunk_id = item.get("chunk_id", f"chunk_{i}")
            text = item.get("text", "")
            
            context += f"\n[DOC {doc_id}] {text[:800]}"
            citations.append(chunk_id or doc_id)
        
        # Генерируем ответ
        synthesis_prompt = f"""
        Используя найденную информацию, дай исчерпывающий ответ на вопрос пользователя.
        
        ВОПРОС: {state.original_query}
        
        НАЙДЕННАЯ ИНФОРМАЦИЯ:{context}
        
        ТРЕБОВАНИЯ:
        1. Отвечай точно на поставленный вопрос
        2. Используй только информацию из контекста
        3. Цитируй источники в формате [doc_id]
        4. Если информации недостаточно, честно скажи об этом
        5. Структурируй ответ логично и понятно
        """
        
        try:
            answer = await self.llm.complete(
                "Ты - эксперт-аналитик, который синтезирует информацию из документов.",
                synthesis_prompt
            )
            
            return {
                "answer": answer,
                "citations": citations,
                "sources_used": len(all_content),
                "strategies_tried": [s.value for s in state.strategies_tried],
                "total_iterations": state.iteration,
                "confidence_score": sum(r.confidence for r in state.results_history) / len(state.results_history) if state.results_history else 0,
                "search_metadata": {
                    "total_search_time": sum(r.metadata.get("search_time", 0) for r in state.results_history),
                    "strategies_performance": {
                        r.strategy.value: {
                            "relevance": r.relevance_score,
                            "confidence": r.confidence,
                            "results_count": len(r.content)
                        } for r in state.results_history
                    }
                }
            }
            
        except Exception as e:
            print(f"⚠️ Synthesis Agent error: {e}")
            return {
                "answer": f"Извините, произошла ошибка при синтезе ответа: {e}",
                "citations": citations,
                "error": True
            }


class AgenticRAGSystem:
    """🚀 Главный класс Agentic RAG системы"""
    
    def __init__(self, corpus: HybridCorpus, graph: GraphIndex):
        self.corpus = corpus
        self.graph = graph
        self.llm = LLM()
        
        # Инициализируем агентов
        self.router = RouterAgent(self.llm)
        self.retriever = RetrievalAgent(corpus, graph)
        self.rewriter = QueryRewriterAgent(self.llm)
        self.evaluator = EvaluationAgent(self.llm)
        self.synthesizer = SynthesisAgent(self.llm)
    
    async def process_query(self, query: str, max_iterations: int = 5, confidence_threshold: float = 0.7) -> Dict[str, Any]:
        """Основной метод обработки запроса через агентную систему"""
        
        print(f"🚀 Agentic RAG: Starting query processing: '{query[:50]}...'")
        
        # Инициализируем состояние
        state = AgentState(
            original_query=query,
            current_query=query,
            iteration=0,
            strategies_tried=[],
            results_history=[],
            accumulated_context="",
            confidence_threshold=confidence_threshold,
            max_iterations=max_iterations
        )
        
        start_time = time.time()
        
        # Основной цикл агентной обработки
        while state.iteration < max_iterations:
            state.iteration += 1
            print(f"\n🔄 Iteration {state.iteration}: Query='{state.current_query[:50]}...'")
            
            # Шаг 1: Router Agent выбирает стратегию
            strategy = await self.router.analyze_query(state.current_query, state)
            print(f"🎯 Router Agent chose: {strategy.value}")
            
            # Шаг 2: Retrieval Agent выполняет поиск
            result = await self.retriever.execute_search(state.current_query, strategy)
            state.strategies_tried.append(strategy)
            state.results_history.append(result)
            
            print(f"🔍 Retrieval Agent found: {len(result.content)} results, relevance={result.relevance_score:.2f}, confidence={result.confidence:.2f}")
            
            # Шаг 3: Evaluation Agent оценивает результаты
            decision, reason = await self.evaluator.evaluate_results(state, result)
            print(f"📊 Evaluation Agent decision: {decision.value} - {reason}")
            
            # Шаг 4: Принимаем решение
            if decision == AgentDecision.SUFFICIENT:
                print("✅ Sufficient results found, proceeding to synthesis")
                break
            elif decision == AgentDecision.REWRITE_QUERY:
                state.current_query = await self.rewriter.rewrite_query(state, result)
                print(f"✏️ Query rewritten to: '{state.current_query[:50]}...'")
            elif decision == AgentDecision.CHANGE_STRATEGY:
                print("🔄 Changing strategy, router will choose new one")
                continue
            else:
                print("🔄 Continuing with current approach")
        
        # Шаг 5: Synthesis Agent генерирует финальный ответ
        print(f"\n🔄 Synthesis Agent: Combining results from {len(state.results_history)} searches")
        final_response = await self.synthesizer.synthesize_response(state)
        
        # Добавляем метаданные процесса
        final_response.update({
            "agentic_metadata": {
                "total_time": time.time() - start_time,
                "iterations_used": state.iteration,
                "strategies_tried": [s.value for s in state.strategies_tried],
                "final_query": state.current_query,
                "query_evolution": [state.original_query, state.current_query] if state.current_query != state.original_query else [state.original_query]
            }
        })
        
        print(f"🏁 Agentic RAG completed in {final_response['agentic_metadata']['total_time']:.2f}s with {state.iteration} iterations")
        
        return final_response
    
    async def stream_query(self, query: str, max_iterations: int = 5):
        """Потоковая версия обработки запроса с промежуточными результатами"""
        
        yield {"type": "agentic_start", "data": {"query": query, "max_iterations": max_iterations}}
        
        # Инициализируем состояние
        state = AgentState(
            original_query=query,
            current_query=query,
            iteration=0,
            strategies_tried=[],
            results_history=[],
            accumulated_context="",
            max_iterations=max_iterations
        )
        
        # Основной цикл с потоковым выводом
        while state.iteration < state.max_iterations:
            state.iteration += 1
            
            yield {"type": "iteration_start", "data": {"iteration": state.iteration, "current_query": state.current_query}}
            
            # Router Agent
            strategy = await self.router.analyze_query(state.current_query, state)
            yield {"type": "strategy_selected", "data": {"strategy": strategy.value, "reason": f"Iteration {state.iteration}"}}
            
            # Retrieval Agent
            result = await self.retriever.execute_search(state.current_query, strategy)
            state.strategies_tried.append(strategy)
            state.results_history.append(result)
            
            yield {"type": "search_completed", "data": {
                "strategy": strategy.value,
                "results_count": len(result.content),
                "relevance_score": result.relevance_score,
                "confidence": result.confidence,
                "search_time": result.metadata.get("search_time", 0)
            }}
            
            # Evaluation Agent
            decision, reason = await self.evaluator.evaluate_results(state, result)
            yield {"type": "evaluation", "data": {"decision": decision.value, "reason": reason}}
            
            if decision == AgentDecision.SUFFICIENT:
                break
            elif decision == AgentDecision.REWRITE_QUERY:
                state.current_query = await self.rewriter.rewrite_query(state, result)
                yield {"type": "query_rewritten", "data": {"new_query": state.current_query}}
        
        # Synthesis
        yield {"type": "synthesis_start", "data": {"total_results": sum(len(r.content) for r in state.results_history)}}
        
        final_response = await self.synthesizer.synthesize_response(state)
        
        yield {"type": "agentic_complete", "data": final_response}
