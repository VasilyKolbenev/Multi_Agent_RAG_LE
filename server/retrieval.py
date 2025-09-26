import os, re, json
import numpy as np
from typing import List, Tuple, Optional, Set, Dict, Any
from rank_bm25 import BM25Okapi
import faiss
from openai import OpenAI
from . import config # Импортируем наш новый конфиг

from dataclasses import dataclass

@dataclass(kw_only=True)
class Document:
    id: str
    text: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class EmbeddedDocument(Document):
    embedding: List[float]


def update_document_in_corpus(corpus: Any, doc_id: str, new_text: str):
    """Заглушка для обновления документа в корпусе."""
    print(f"Stub: Updating document {doc_id} with new text (length: {len(new_text)})")
    # Здесь должна быть реальная логика обновления

def get_corpus_stats(corpus: Any) -> Dict[str, Any]:
    """Заглушка для получения статистики корпуса."""
    return {"total_documents": len(corpus.list_docs()), "total_chunks": len(corpus.chunks)}

def clear_corpus(corpus: Any):
    """Заглушка для очистки корпуса."""
    print("Stub: Clearing corpus")
    corpus.docs = {}
    corpus.chunks = {}
    corpus.index = None
    corpus.bm25 = None
    corpus._save() # Сохраняем пустое состояние


# --- Константы и Клиенты ---
DATA_DIR = os.environ.get("DATA_DIR", "data")
FAISS_INDEX_PATH = os.path.join(DATA_DIR, "faiss.index")
CHUNK_MAP_PATH = os.path.join(DATA_DIR, "chunk_map.json")
DOCS_PATH = os.path.join(DATA_DIR, "docs.json")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")

os.makedirs(DATA_DIR, exist_ok=True)

# Инициализация клиента OpenAI (теперь безопасная)
openai_client = OpenAI(api_key=config.OPENAI_API_KEY)


# --- Утилиты ---

def _get_embedding(text: str):
    try:
        response = openai_client.embeddings.create(input=[text.replace("\n", " ")], model=config.EMBEDDING_MODEL)
        return response.data[0].embedding
    except Exception as e:
        print(f"[EMBEDDING] Error creating embedding: {e}")
        # Возвращаем фиктивный embedding для продолжения работы
        return [0.0] * 1536  # Размерность text-embedding-3-small

def _semantic_chunking(text: str, max_chunk_size=1500):
    """
    Разбивает текст на чанки, безопасные для embedding модели.
    
    Учитывая лимит text-embedding-3-small в 8192 токена,
    мы используем консервативный размер чанка в 1500 символов (~375 токенов).
    """
    # Если весь текст помещается в один чанк
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    
    # Сначала пробуем разбить по абзацам
    paragraphs = text.split('\n\n')
    current_chunk = ""
    
    for paragraph in paragraphs:
        if not paragraph.strip():
            continue
            
        # Если абзац слишком большой, разбиваем его по предложениям
        if len(paragraph) > max_chunk_size:
            # Сохраняем текущий чанк, если он есть
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            
            # Разбиваем большой абзац по предложениям
            sentences = re.split(r'[.!?]+', paragraph)
            for sentence in sentences:
                if not sentence.strip():
                    continue
                    
                sentence = sentence.strip() + '.'
                
                # Если предложение слишком длинное, принудительно разрезаем
                if len(sentence) > max_chunk_size:
                    # Разбиваем по словам
                    words = sentence.split()
                    temp_chunk = ""
                    for word in words:
                        if len(temp_chunk) + len(word) + 1 <= max_chunk_size:
                            temp_chunk += word + " "
                        else:
                            if temp_chunk:
                                chunks.append(temp_chunk.strip())
                            temp_chunk = word + " "
                    if temp_chunk:
                        chunks.append(temp_chunk.strip())
                else:
                    # Обычное предложение
                    if len(current_chunk) + len(sentence) + 1 <= max_chunk_size:
                        current_chunk += sentence + " "
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence + " "
        else:
            # Обычный абзац
            if len(current_chunk) + len(paragraph) + 2 <= max_chunk_size:
                current_chunk += paragraph + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\n\n"
    
    # Добавляем последний чанк
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    # Фильтруем слишком короткие чанки (менее 50 символов)
    chunks = [chunk for chunk in chunks if len(chunk) >= 50]
    
    return chunks

# --- Основной класс ---

class HybridCorpus:
    def __init__(self):
        self.docs: Dict[str, str] = {}
        self.chunks: Dict[str, Dict[str, Any]] = {} # chunk_id -> {doc_id, text}

        self.index = None
        self.bm25 = None
        
        self._load()

    def _load(self):
        if os.path.exists(FAISS_INDEX_PATH):
            self.index = faiss.read_index(FAISS_INDEX_PATH)
        if os.path.exists(CHUNK_MAP_PATH):
            with open(CHUNK_MAP_PATH, 'r', encoding='utf-8') as f:
                self.chunks = json.load(f)
        if os.path.exists(DOCS_PATH):
            with open(DOCS_PATH, 'r', encoding='utf-8') as f:
                self.docs = json.load(f)
        
        self._reindex_bm25()

    def _save(self):
        if self.index:
            faiss.write_index(self.index, FAISS_INDEX_PATH)
        with open(CHUNK_MAP_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=4)
        with open(DOCS_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.docs, f, ensure_ascii=False, indent=4)

    def ingest_text(self, doc_id: str, text: str):
        self.docs[doc_id] = text
        chunk_texts = _semantic_chunking(text)
        
        if not chunk_texts: return

        embeddings = [_get_embedding(chunk) for chunk in chunk_texts]
        
        # Обновляем FAISS индекс
        if self.index is None:
            dimension = len(embeddings[0])
            self.index = faiss.IndexFlatL2(dimension)
            self.index = faiss.IndexIDMap(self.index)

        # Создаем уникальные числовые ID для FAISS
        start_id = max([int(k) for k in self.chunks.keys()] + [0]) + 1
        ids = np.arange(start_id, start_id + len(embeddings))
        self.index.add_with_ids(np.array(embeddings).astype('float32'), ids)

        # Обновляем маппинг
        for i, chunk_text in enumerate(chunk_texts):
            self.chunks[str(start_id + i)] = {"doc_id": doc_id, "text": chunk_text}
            
        self._reindex_bm25()
        self._save()

    def _reindex_bm25(self):
        def tok(s: str) -> List[str]:
            return re.findall(r"[\w']+", s.lower())
        
        tokenized_chunks = [tok(c['text']) for c in self.chunks.values()]
        if tokenized_chunks:
            self.bm25 = BM25Okapi(tokenized_chunks)

    def search(self, query: str, k: int = 10, allowed_docs: Optional[Set[str]] = None) -> List[Dict[str, Any]]:
        # Проверяем, что индекс существует
        if self.index is None or len(self.chunks) == 0:
            return []
            
        # 1. Dense Search (FAISS)
        query_embedding = np.array([_get_embedding(query)]).astype('float32')
        distances, ids = self.index.search(query_embedding, k)
        dense_results = [(str(faiss_id), rank) for rank, faiss_id in enumerate(ids[0]) if faiss_id != -1]
        
        # 2. Sparse Search (BM25) - по всем чанкам
        bm25_results = []
        if self.bm25:
            qtok = re.findall(r"[\w']+", query.lower())
            scores = self.bm25.get_scores(qtok)
            top_n_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
            bm25_results = [(str(i), rank) for rank, i in enumerate(top_n_indices)]

        # 3. RRF Merge
        merged_ids = self._rrf_merge([dense_results, bm25_results])
        
        final_chunks = []
        for chunk_id in merged_ids:
            if chunk_id in self.chunks:
                chunk_data = self.chunks[chunk_id]
                # Фильтрация по allowed_docs если указана
                if allowed_docs is None or chunk_data['doc_id'] in allowed_docs:
                    final_chunks.append({"chunk_id": chunk_id, "doc_id": chunk_data['doc_id'], "text": chunk_data['text']})
        
        return final_chunks[:k]

    def _rrf_merge(self, ranklists: List[List[Tuple[str, int]]], const_k=60) -> List[str]:
        scores = {}
        for lst in ranklists:
            for doc_id, r in lst:
                scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (const_k + (r + 1))
        return [doc for doc, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)]

    def list_docs(self) -> List[Dict[str, Any]]:
        return [{"doc_id": doc_id, "text_preview": text[:100] + "...", "text_length": len(text)} for doc_id, text in self.docs.items()]

    def delete_doc(self, doc_id: str) -> bool:
        # Удаление из FAISS требует пересоздания индекса, это сложная операция.
        # Пока что просто удаляем из словарей, но вектор останется в индексе.
        # Для полноценного удаления нужен более сложный механизм.
        chunks_to_delete = {cid for cid, c in self.chunks.items() if c['doc_id'] == doc_id}
        if not chunks_to_delete: return False
        
        self.chunks = {cid: c for cid, c in self.chunks.items() if cid not in chunks_to_delete}
        if doc_id in self.docs:
            del self.docs[doc_id]
            
        self._reindex_bm25()
        self._save()
        # self.index.remove_ids(...) -> так можно удалять, но нужно управлять ID
        return True
