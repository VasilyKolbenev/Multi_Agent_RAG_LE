import os, re, json
import numpy as np
from typing import List, Tuple, Optional, Set, Dict, Any
from rank_bm25 import BM25Okapi
import faiss
from openai import OpenAI

# --- Константы и Клиенты ---
DATA_DIR = os.environ.get("DATA_DIR", "data")
FAISS_INDEX_PATH = os.path.join(DATA_DIR, "faiss.index")
CHUNK_MAP_PATH = os.path.join(DATA_DIR, "chunk_map.json")
DOCS_PATH = os.path.join(DATA_DIR, "docs.json")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")

os.makedirs(DATA_DIR, exist_ok=True)

# Инициализация клиента OpenAI (должен быть здесь, чтобы использовать ключ)
try:
    openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
except Exception as e:
    print(f"CRITICAL: Failed to initialize OpenAI client: {e}")
    openai_client = None

# --- Утилиты ---

def _get_embedding(text: str):
    if not openai_client:
        raise ConnectionError("OpenAI client not initialized. Check API key.")
    response = openai_client.embeddings.create(input=[text.replace("\n", " ")], model=EMBEDDING_MODEL)
    return response.data[0].embedding

def _semantic_chunking(text: str, min_chunk_size=200, max_chunk_size=400):
    # Простой семантический чанкинг по параграфам
    chunks = []
    current_chunk = ""
    for paragraph in text.split('\n\n'):
        if not paragraph.strip():
            continue
        if len(current_chunk) + len(paragraph) < max_chunk_size:
            current_chunk += paragraph + "\n\n"
        else:
            if len(current_chunk) > min_chunk_size:
                chunks.append(current_chunk.strip())
            current_chunk = paragraph + "\n\n"
    if len(current_chunk) > min_chunk_size:
        chunks.append(current_chunk.strip())
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

    def search(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
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
