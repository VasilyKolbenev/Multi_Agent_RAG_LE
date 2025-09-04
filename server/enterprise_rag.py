"""
Enterprise RAG System
Интеграция MultiAgent-RAG с внешними источниками данных
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from .connectors import ConnectorManager, DataSource, ExtractedRecord
from .langx import LangExtract
from .storage import VectorStore
from .agents import AgentSystem

logger = logging.getLogger(__name__)

@dataclass
class SyncJob:
    """Задача синхронизации данных"""
    source_id: str
    schedule: str  # cron-like: "0 */6 * * *" (каждые 6 часов)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    enabled: bool = True

class EnterpriseRAGSystem:
    """
    Корпоративная RAG система с поддержкой множественных источников данных
    """
    
    def __init__(self, vector_store: VectorStore, lang_extract: LangExtract, agent_system: AgentSystem):
        self.vector_store = vector_store
        self.lang_extract = lang_extract
        self.agent_system = agent_system
        self.connector_manager = ConnectorManager()
        self.sync_jobs: Dict[str, SyncJob] = {}
        
        # Статистика
        self.stats = {
            'total_records_processed': 0,
            'total_entities_extracted': 0,
            'sources_synced': 0,
            'last_full_sync': None
        }
    
    async def add_data_source(self, data_source: DataSource, sync_schedule: str = "0 */6 * * *"):
        """
        Добавление нового источника данных
        
        Args:
            data_source: Конфигурация источника данных
            sync_schedule: Расписание синхронизации (cron format)
        """
        # Регистрируем источник в менеджере коннекторов
        self.connector_manager.register_data_source(data_source)
        
        # Создаем задачу синхронизации
        sync_job = SyncJob(
            source_id=data_source.id,
            schedule=sync_schedule,
            next_run=datetime.now() + timedelta(minutes=5)  # Первый запуск через 5 минут
        )
        self.sync_jobs[data_source.id] = sync_job
        
        logger.info(f"Added data source: {data_source.name} with sync schedule: {sync_schedule}")
        
        # Тестируем соединение
        test_result = await self.connector_manager.test_connection(data_source.id)
        if not test_result:
            logger.warning(f"Connection test failed for data source: {data_source.name}")
        
        return test_result
    
    async def sync_data_source(self, source_id: str, limit: int = 1000) -> Dict[str, Any]:
        """
        Синхронизация конкретного источника данных
        
        Returns:
            Статистика синхронизации
        """
        start_time = datetime.now()
        sync_stats = {
            'source_id': source_id,
            'records_processed': 0,
            'entities_extracted': 0,
            'errors': [],
            'duration_seconds': 0,
            'success': False
        }
        
        try:
            logger.info(f"Starting sync for data source: {source_id}")
            
            # Извлекаем записи из источника
            records = await self.connector_manager.extract_from_source(source_id, limit)
            
            if not records:
                logger.warning(f"No records found in data source: {source_id}")
                sync_stats['success'] = True
                return sync_stats
            
            # Обрабатываем записи батчами
            batch_size = 50
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                await self._process_record_batch(batch, sync_stats)
            
            # Обновляем общую статистику
            self.stats['total_records_processed'] += sync_stats['records_processed']
            self.stats['total_entities_extracted'] += sync_stats['entities_extracted']
            self.stats['sources_synced'] += 1
            
            sync_stats['success'] = True
            logger.info(f"Sync completed for {source_id}: {sync_stats['records_processed']} records processed")
            
        except Exception as e:
            error_msg = f"Sync failed for {source_id}: {str(e)}"
            logger.error(error_msg)
            sync_stats['errors'].append(error_msg)
        
        finally:
            sync_stats['duration_seconds'] = (datetime.now() - start_time).total_seconds()
            
            # Обновляем время последнего запуска
            if source_id in self.sync_jobs:
                self.sync_jobs[source_id].last_run = datetime.now()
        
        return sync_stats
    
    async def _process_record_batch(self, records: List[ExtractedRecord], sync_stats: Dict[str, Any]):
        """Обработка батча записей"""
        
        for record in records:
            try:
                # Пропускаем пустые записи
                if not record.content or len(record.content.strip()) < 10:
                    continue
                
                # Извлекаем сущности с помощью LangExtract
                entities_result = await self.lang_extract.extract_entities_async(
                    text=record.content,
                    task_prompt="Извлеки людей, компании, места, даты, продукты и ключевые термины из этого текста"
                )
                
                if entities_result.get('success') and entities_result.get('items'):
                    record.entities = entities_result['items']
                    sync_stats['entities_extracted'] += len(record.entities)
                
                # Добавляем в векторное хранилище
                document_id = f"{record.source_id}_{record.record_id}"
                
                await self.vector_store.add_document(
                    doc_id=document_id,
                    title=record.title,
                    content=record.content,
                    metadata={
                        **record.metadata,
                        'entities': record.entities or [],
                        'source_timestamp': record.timestamp.isoformat() if record.timestamp else None
                    }
                )
                
                sync_stats['records_processed'] += 1
                
                # Логируем прогресс каждые 10 записей
                if sync_stats['records_processed'] % 10 == 0:
                    logger.info(f"Processed {sync_stats['records_processed']} records from {record.source_id}")
                
            except Exception as e:
                error_msg = f"Error processing record {record.record_id}: {str(e)}"
                logger.error(error_msg)
                sync_stats['errors'].append(error_msg)
    
    async def sync_all_sources(self) -> Dict[str, Any]:
        """Синхронизация всех активных источников данных"""
        
        start_time = datetime.now()
        overall_stats = {
            'total_sources': 0,
            'successful_syncs': 0,
            'failed_syncs': 0,
            'total_records': 0,
            'total_entities': 0,
            'duration_seconds': 0,
            'source_results': {}
        }
        
        try:
            active_sources = [
                source_id for source_id, job in self.sync_jobs.items() 
                if job.enabled
            ]
            
            overall_stats['total_sources'] = len(active_sources)
            
            # Синхронизируем источники параллельно (ограниченно)
            semaphore = asyncio.Semaphore(3)  # Максимум 3 параллельных синхронизации
            
            async def sync_with_semaphore(source_id: str):
                async with semaphore:
                    return await self.sync_data_source(source_id)
            
            # Запускаем синхронизацию
            tasks = [sync_with_semaphore(source_id) for source_id in active_sources]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Обрабатываем результаты
            for source_id, result in zip(active_sources, results):
                if isinstance(result, Exception):
                    logger.error(f"Sync failed for {source_id}: {result}")
                    overall_stats['failed_syncs'] += 1
                    overall_stats['source_results'][source_id] = {
                        'success': False,
                        'error': str(result)
                    }
                else:
                    overall_stats['source_results'][source_id] = result
                    
                    if result['success']:
                        overall_stats['successful_syncs'] += 1
                        overall_stats['total_records'] += result['records_processed']
                        overall_stats['total_entities'] += result['entities_extracted']
                    else:
                        overall_stats['failed_syncs'] += 1
            
            # Обновляем общую статистику
            self.stats['last_full_sync'] = datetime.now()
            
            logger.info(f"Full sync completed: {overall_stats['successful_syncs']}/{overall_stats['total_sources']} sources successful")
            
        except Exception as e:
            logger.error(f"Error during full sync: {e}")
        
        finally:
            overall_stats['duration_seconds'] = (datetime.now() - start_time).total_seconds()
        
        return overall_stats
    
    async def search_across_sources(self, query: str, source_filters: List[str] = None) -> Dict[str, Any]:
        """
        Поиск по всем источникам данных с возможностью фильтрации
        
        Args:
            query: Поисковый запрос
            source_filters: Список ID источников для фильтрации (опционально)
        """
        
        # Используем агентную систему для обработки запроса
        search_results = await self.agent_system.process_query(
            query=query,
            metadata_filters={'source_id': source_filters} if source_filters else None
        )
        
        # Группируем результаты по источникам
        results_by_source = {}
        
        for result in search_results.get('documents', []):
            source_id = result.get('metadata', {}).get('source_id', 'unknown')
            
            if source_id not in results_by_source:
                results_by_source[source_id] = []
            
            results_by_source[source_id].append(result)
        
        return {
            'query': query,
            'total_results': len(search_results.get('documents', [])),
            'sources_found': len(results_by_source),
            'results_by_source': results_by_source,
            'agent_analysis': search_results.get('analysis', ''),
            'entities_found': search_results.get('entities', [])
        }
    
    async def get_enterprise_analytics(self) -> Dict[str, Any]:
        """Получение аналитики по корпоративным данным"""
        
        # Статистика по источникам
        source_stats = {}
        for source_id, data_source in self.connector_manager.data_sources.items():
            source_stats[source_id] = {
                'name': data_source.name,
                'type': data_source.type,
                'enabled': data_source.enabled,
                'last_sync': data_source.last_sync.isoformat() if data_source.last_sync else None,
                'connection_status': await self.connector_manager.connectors[source_id].test_connection()
            }
        
        # Статистика векторного хранилища
        vector_stats = await self.vector_store.get_stats()
        
        # Топ сущности
        top_entities = await self._get_top_entities()
        
        return {
            'overview': self.stats,
            'sources': source_stats,
            'vector_store': vector_stats,
            'top_entities': top_entities,
            'sync_jobs': {
                job_id: {
                    'schedule': job.schedule,
                    'last_run': job.last_run.isoformat() if job.last_run else None,
                    'next_run': job.next_run.isoformat() if job.next_run else None,
                    'enabled': job.enabled
                }
                for job_id, job in self.sync_jobs.items()
            }
        }
    
    async def _get_top_entities(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Получение топ сущностей по частоте упоминания"""
        # Это упрощенная версия - в реальности нужна более сложная аналитика
        
        # Здесь можно добавить запросы к векторному хранилищу
        # для подсчета частоты упоминания сущностей
        
        return [
            {'entity': 'Компания ABC', 'type': 'ORG', 'count': 145, 'sources': ['company_db', 'company_wiki']},
            {'entity': 'Иван Петров', 'type': 'PERSON', 'count': 89, 'sources': ['company_db']},
            {'entity': 'Москва', 'type': 'LOCATION', 'count': 67, 'sources': ['company_db', 'company_wiki']},
            # ... более реальные данные будут из анализа документов
        ]
    
    async def schedule_sync(self, source_id: str, immediate: bool = False):
        """Планирование синхронизации источника"""
        
        if source_id not in self.sync_jobs:
            raise ValueError(f"Sync job not found for source: {source_id}")
        
        if immediate:
            # Немедленная синхронизация
            return await self.sync_data_source(source_id)
        else:
            # Планируем на следующий интервал
            self.sync_jobs[source_id].next_run = datetime.now() + timedelta(minutes=5)
            logger.info(f"Scheduled sync for {source_id}")
            return {"scheduled": True, "next_run": self.sync_jobs[source_id].next_run}
    
    async def cleanup(self):
        """Очистка ресурсов"""
        await self.connector_manager.cleanup()


# Пример настройки Enterprise RAG
async def setup_enterprise_rag_example():
    """Пример настройки корпоративной RAG системы"""
    
    # Инициализируем компоненты (предполагаем, что они уже созданы)
    # vector_store = VectorStore()
    # lang_extract = LangExtract()
    # agent_system = AgentSystem()
    
    # enterprise_rag = EnterpriseRAGSystem(vector_store, lang_extract, agent_system)
    
    # Настраиваем источники данных
    
    # 1. PostgreSQL с клиентскими данными
    client_db_source = DataSource(
        id="client_database",
        name="Client Database",
        type="postgresql",
        connection_params={
            'host': 'prod-db.company.com',
            'port': 5432,
            'database': 'clients',
            'user': 'rag_reader',
            'password': 'secure_password',
            'table': 'client_profiles',
            'extract_query': """
                SELECT 
                    client_id::text as record_id,
                    CONCAT(first_name, ' ', last_name) as title,
                    CONCAT(
                        'Клиент: ', first_name, ' ', last_name, '. ',
                        'Компания: ', COALESCE(company_name, 'Не указана'), '. ',
                        'Регион: ', COALESCE(region, 'Не указан'), '. ',
                        'Комментарии: ', COALESCE(notes, 'Нет комментариев')
                    ) as content,
                    created_at,
                    updated_at
                FROM client_profiles 
                WHERE LENGTH(COALESCE(notes, '')) > 10
                   OR company_name IS NOT NULL
                ORDER BY updated_at DESC 
                LIMIT $1
            """
        }
    )
    
    # 2. Confluence с технической документацией
    confluence_source = DataSource(
        id="tech_docs",
        name="Technical Documentation",
        type="confluence",
        connection_params={
            'base_url': 'https://company.atlassian.net/wiki',
            'username': 'rag-bot@company.com',
            'api_token': 'ATATT3xFfGF0...',  # Реальный токен
            'space_key': 'TECH'
        }
    )
    
    # 3. PostgreSQL с логами транзакций
    transaction_db_source = DataSource(
        id="transaction_logs",
        name="Transaction Logs",
        type="postgresql",
        connection_params={
            'host': 'analytics-db.company.com',
            'database': 'analytics',
            'user': 'rag_analytics',
            'password': 'analytics_password',
            'table': 'transaction_summary',
            'extract_query': """
                SELECT 
                    transaction_id::text as record_id,
                    CONCAT('Транзакция #', transaction_id) as title,
                    CONCAT(
                        'Сумма: ', amount, ' руб. ',
                        'Клиент: ', client_name, '. ',
                        'Категория: ', category, '. ',
                        'Статус: ', status, '. ',
                        CASE WHEN description IS NOT NULL 
                             THEN CONCAT('Описание: ', description)
                             ELSE '' END
                    ) as content,
                    created_at,
                    updated_at
                FROM transaction_summary 
                WHERE amount > 1000  -- Только крупные транзакции
                   OR status = 'suspicious'  -- Или подозрительные
                ORDER BY created_at DESC 
                LIMIT $1
            """
        }
    )
    
    # Добавляем источники в систему
    # await enterprise_rag.add_data_source(client_db_source, "0 */4 * * *")  # Каждые 4 часа
    # await enterprise_rag.add_data_source(confluence_source, "0 2 * * *")   # Каждый день в 2:00
    # await enterprise_rag.add_data_source(transaction_db_source, "0 */1 * * *")  # Каждый час
    
    # Запускаем первоначальную синхронизацию
    # sync_results = await enterprise_rag.sync_all_sources()
    # print("Initial sync results:", sync_results)
    
    # Пример поиска
    # search_results = await enterprise_rag.search_across_sources(
    #     query="Найди всех клиентов из Москвы с подозрительными транзакциями",
    #     source_filters=["client_database", "transaction_logs"]
    # )
    
    return "Enterprise RAG configured successfully"

if __name__ == "__main__":
    asyncio.run(setup_enterprise_rag_example())
