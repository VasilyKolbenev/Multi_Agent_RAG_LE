"""
Enterprise Data Connectors for MultiAgent-RAG Pro
Поддержка PostgreSQL, Confluence, Wiki и других источников данных
"""

import asyncio
import asyncpg
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class DataSource:
    """Описание источника данных"""
    id: str
    name: str
    type: str  # 'postgresql', 'confluence', 'wiki', 'filesystem'
    connection_params: Dict[str, Any]
    enabled: bool = True
    last_sync: Optional[datetime] = None

@dataclass
class ExtractedRecord:
    """Извлеченная запись из источника данных"""
    source_id: str
    record_id: str
    title: str
    content: str
    metadata: Dict[str, Any]
    entities: List[Dict[str, Any]] = None
    timestamp: datetime = None

class BaseConnector(ABC):
    """Базовый класс для всех коннекторов"""
    
    def __init__(self, data_source: DataSource):
        self.data_source = data_source
        self.connection = None
    
    @abstractmethod
    async def connect(self) -> bool:
        """Установить соединение с источником данных"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Закрыть соединение"""
        pass
    
    @abstractmethod
    async def extract_records(self, limit: int = 1000) -> List[ExtractedRecord]:
        """Извлечь записи из источника"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Проверить соединение"""
        pass

class PostgreSQLConnector(BaseConnector):
    """Коннектор для PostgreSQL баз данных"""
    
    async def connect(self) -> bool:
        try:
            params = self.data_source.connection_params
            self.connection = await asyncpg.connect(
                host=params.get('host', 'localhost'),
                port=params.get('port', 5432),
                database=params['database'],
                user=params['user'],
                password=params['password']
            )
            logger.info(f"Connected to PostgreSQL: {params['database']}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            return False
    
    async def disconnect(self):
        if self.connection:
            await self.connection.close()
            self.connection = None
    
    async def extract_records(self, limit: int = 1000) -> List[ExtractedRecord]:
        """
        Извлечение записей из PostgreSQL
        Поддерживает настраиваемые SQL запросы для извлечения текстовых данных
        """
        if not self.connection:
            await self.connect()
        
        records = []
        params = self.data_source.connection_params
        
        # Настраиваемый SQL запрос для извлечения данных
        query = params.get('extract_query', """
            SELECT 
                id::text as record_id,
                COALESCE(title, name, subject, '') as title,
                COALESCE(content, description, text, body, '') as content,
                created_at,
                updated_at
            FROM {table}
            WHERE LENGTH(COALESCE(content, description, text, body, '')) > 50
            ORDER BY updated_at DESC
            LIMIT $1
        """.format(table=params.get('table', 'documents')))
        
        try:
            rows = await self.connection.fetch(query, limit)
            
            for row in rows:
                record = ExtractedRecord(
                    source_id=self.data_source.id,
                    record_id=str(row['record_id']),
                    title=row['title'] or f"Record {row['record_id']}",
                    content=row['content'] or '',
                    metadata={
                        'table': params.get('table'),
                        'created_at': row.get('created_at'),
                        'updated_at': row.get('updated_at'),
                        'source_type': 'postgresql'
                    },
                    timestamp=row.get('updated_at') or row.get('created_at')
                )
                records.append(record)
                
        except Exception as e:
            logger.error(f"Error extracting PostgreSQL records: {e}")
        
        return records
    
    async def test_connection(self) -> bool:
        try:
            if not self.connection:
                return await self.connect()
            
            # Простой тест запрос
            await self.connection.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"PostgreSQL connection test failed: {e}")
            return False

class ConfluenceConnector(BaseConnector):
    """Коннектор для Confluence"""
    
    async def connect(self) -> bool:
        # Confluence использует HTTP API, соединение не требуется
        return True
    
    async def disconnect(self):
        pass
    
    async def extract_records(self, limit: int = 1000) -> List[ExtractedRecord]:
        """
        Извлечение страниц из Confluence через REST API
        """
        records = []
        params = self.data_source.connection_params
        
        base_url = params['base_url'].rstrip('/')
        username = params['username']
        api_token = params['api_token']
        space_key = params.get('space_key', '')
        
        # API endpoint для получения контента
        url = f"{base_url}/rest/api/content"
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        auth = aiohttp.BasicAuth(username, api_token)
        
        try:
            async with aiohttp.ClientSession() as session:
                params_dict = {
                    'limit': min(limit, 100),  # Confluence API limit
                    'expand': 'body.storage,version,space'
                }
                
                if space_key:
                    params_dict['spaceKey'] = space_key
                
                async with session.get(url, headers=headers, auth=auth, params=params_dict) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for page in data.get('results', []):
                            # Извлекаем текст из HTML контента
                            content = self._extract_text_from_html(
                                page.get('body', {}).get('storage', {}).get('value', '')
                            )
                            
                            record = ExtractedRecord(
                                source_id=self.data_source.id,
                                record_id=page['id'],
                                title=page['title'],
                                content=content,
                                metadata={
                                    'space': page.get('space', {}).get('name', ''),
                                    'version': page.get('version', {}).get('number', 1),
                                    'url': f"{base_url}/pages/viewpage.action?pageId={page['id']}",
                                    'source_type': 'confluence'
                                },
                                timestamp=datetime.fromisoformat(
                                    page.get('version', {}).get('when', '').replace('Z', '+00:00')
                                ) if page.get('version', {}).get('when') else None
                            )
                            records.append(record)
                    else:
                        logger.error(f"Confluence API error: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error extracting Confluence records: {e}")
        
        return records
    
    def _extract_text_from_html(self, html_content: str) -> str:
        """Простое извлечение текста из HTML"""
        import re
        
        # Убираем HTML теги
        text = re.sub(r'<[^>]+>', ' ', html_content)
        
        # Убираем лишние пробелы
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    async def test_connection(self) -> bool:
        try:
            params = self.data_source.connection_params
            base_url = params['base_url'].rstrip('/')
            username = params['username']
            api_token = params['api_token']
            
            url = f"{base_url}/rest/api/content"
            headers = {'Accept': 'application/json'}
            auth = aiohttp.BasicAuth(username, api_token)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, auth=auth, params={'limit': 1}) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"Confluence connection test failed: {e}")
            return False

class ConnectorManager:
    """Менеджер для управления всеми коннекторами"""
    
    def __init__(self):
        self.connectors: Dict[str, BaseConnector] = {}
        self.data_sources: Dict[str, DataSource] = {}
    
    def register_data_source(self, data_source: DataSource):
        """Регистрация нового источника данных"""
        self.data_sources[data_source.id] = data_source
        
        # Создаем соответствующий коннектор
        if data_source.type == 'postgresql':
            connector = PostgreSQLConnector(data_source)
        elif data_source.type == 'confluence':
            connector = ConfluenceConnector(data_source)
        else:
            raise ValueError(f"Unsupported data source type: {data_source.type}")
        
        self.connectors[data_source.id] = connector
        logger.info(f"Registered data source: {data_source.name} ({data_source.type})")
    
    async def test_all_connections(self) -> Dict[str, bool]:
        """Тестирование всех соединений"""
        results = {}
        
        for source_id, connector in self.connectors.items():
            try:
                results[source_id] = await connector.test_connection()
            except Exception as e:
                logger.error(f"Connection test failed for {source_id}: {e}")
                results[source_id] = False
        
        return results
    
    async def extract_from_source(self, source_id: str, limit: int = 1000) -> List[ExtractedRecord]:
        """Извлечение данных из конкретного источника"""
        if source_id not in self.connectors:
            raise ValueError(f"Unknown data source: {source_id}")
        
        connector = self.connectors[source_id]
        records = await connector.extract_records(limit)
        
        # Обновляем время последней синхронизации
        self.data_sources[source_id].last_sync = datetime.now()
        
        return records
    
    async def extract_from_all_sources(self, limit_per_source: int = 1000) -> List[ExtractedRecord]:
        """Извлечение данных из всех активных источников"""
        all_records = []
        
        for source_id, data_source in self.data_sources.items():
            if data_source.enabled:
                try:
                    records = await self.extract_from_source(source_id, limit_per_source)
                    all_records.extend(records)
                    logger.info(f"Extracted {len(records)} records from {data_source.name}")
                except Exception as e:
                    logger.error(f"Failed to extract from {data_source.name}: {e}")
        
        return all_records
    
    async def cleanup(self):
        """Закрытие всех соединений"""
        for connector in self.connectors.values():
            try:
                await connector.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting connector: {e}")

# Пример использования
async def example_usage():
    """Пример использования коннекторов"""
    manager = ConnectorManager()
    
    # Настройка PostgreSQL источника
    pg_source = DataSource(
        id="company_db",
        name="Company Database",
        type="postgresql",
        connection_params={
            'host': 'localhost',
            'port': 5432,
            'database': 'company',
            'user': 'rag_user',
            'password': 'secure_password',
            'table': 'documents',
            'extract_query': """
                SELECT 
                    id::text as record_id,
                    title,
                    content,
                    created_at,
                    updated_at
                FROM documents 
                WHERE LENGTH(content) > 100
                ORDER BY updated_at DESC 
                LIMIT $1
            """
        }
    )
    
    # Настройка Confluence источника
    confluence_source = DataSource(
        id="company_wiki",
        name="Company Wiki",
        type="confluence",
        connection_params={
            'base_url': 'https://company.atlassian.net/wiki',
            'username': 'rag@company.com',
            'api_token': 'your_api_token',
            'space_key': 'TECH'  # опционально
        }
    )
    
    # Регистрируем источники
    manager.register_data_source(pg_source)
    manager.register_data_source(confluence_source)
    
    # Тестируем соединения
    test_results = await manager.test_all_connections()
    print("Connection tests:", test_results)
    
    # Извлекаем данные
    all_records = await manager.extract_from_all_sources(limit_per_source=100)
    print(f"Total extracted records: {len(all_records)}")
    
    # Закрываем соединения
    await manager.cleanup()

if __name__ == "__main__":
    asyncio.run(example_usage())
