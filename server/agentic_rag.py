"""
🚀 Agentic RAG System - Simplified Implementation
Интеграция агентной системы для улучшенного поиска и ответов
"""

from typing import List, Dict, Any, AsyncGenerator
import logging

logger = logging.getLogger(__name__)

class AgenticRAGSystem:
    """
    Упрощенная система Agentic RAG
    Использует существующую MultiAgent архитектуру
    """
    
    def __init__(self, corpus, graph_index):
        """Инициализация системы"""
        self.corpus = corpus
        self.graph_index = graph_index
        logger.info("🤖 AgenticRAGSystem initialized")
    
    async def agentic_search(self, query: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        Агентный поиск с итеративным улучшением
        Пока что делегируем существующему MultiAgent
        """
        try:
            # Импортируем здесь, чтобы избежать циклических импортов
            from .agents import MultiAgent
            
            # Создаем временный агент для обработки
            agent = MultiAgent(self.corpus, self.graph_index)
            
            # Используем существующий stream метод
            async for chunk in agent.stream(query, **kwargs):
                yield chunk
                
        except Exception as e:
            logger.error(f"❌ Agentic search error: {e}")
            yield f"❌ Ошибка агентного поиска: {str(e)}"
    
    def get_status(self) -> Dict[str, Any]:
        """Статус системы"""
        return {
            "status": "active",
            "corpus_size": len(self.corpus.chunks) if hasattr(self.corpus, 'chunks') else 0,
            "graph_nodes": len(self.graph_index.nodes) if hasattr(self.graph_index, 'nodes') else 0,
            "version": "4.8.1-hotfix"
        }
