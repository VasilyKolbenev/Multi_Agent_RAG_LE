import os, re
from typing import List, Tuple, Optional, Set, Dict, Any
from rank_bm25 import BM25Okapi
import chromadb
from chromadb.utils import embedding_functions

# --- Утилиты ---

def _read_text(path: str) -> str:
    if path.lower().endswith(('.md', '.txt')):
        return open(path, 'r', encoding='utf-8', errors='ignore').read()
    if path.lower().endswith('.pdf'):
        try:
            import pypdf
            reader = pypdf.PdfReader(path)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            return ""
    return ""

def _semantic_chunking(text: str, min_chunk_size=256, max_chunk_size=512):
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
    def __init__(self, data_dir="data"):
        self.docs: Dict[str, str] = {}  # doc_id -> full_text
        self.chunks: List[Dict[str, Any]] = [] # {chunk_id, doc_id, text}

        # BM25 (Sparse)
        self.bm25 = None
        
        # ChromaDB (Dense)
        chroma_path = os.path.join(data_dir, "chroma_db")
        self.client = chromadb.PersistentClient(path=chroma_path)
        
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set!")

        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=api_key,
            model_name=os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
        )
        
        self.collection = self.client.get_or_create_collection(
            name="rag_collection",
            embedding_function=openai_ef,
            metadata={"hnsw:space": "cosine"}
        )
        self._load_from_db()

    def _load_from_db(self):
        # Загрузка чанков из ChromaDB для BM25 и для быстрого доступа
        db_chunks = self.collection.get(include=["metadatas", "documents"])
        if db_chunks and db_chunks['ids']:
            for i, chunk_id in enumerate(db_chunks['ids']):
                doc_id = db_chunks['metadatas'][i]['doc_id']
                text = db_chunks['documents'][i]
                self.chunks.append({"chunk_id": chunk_id, "doc_id": doc_id, "text": text})
                if doc_id not in self.docs:
                    # Приблизительно восстанавливаем полный текст
                    self.docs[doc_id] = self.docs.get(doc_id, "") + text + "\n\n"
            self._reindex_bm25()

    def ingest_text(self, doc_id: str, text: str):
        self.docs[doc_id] = text
        new_chunks = []
        
        chunk_texts = _semantic_chunking(text)
        for i, chunk_text in enumerate(chunk_texts):
            chunk_id = f"{doc_id}_chunk_{i}"
            new_chunks.append({"chunk_id": chunk_id, "doc_id": doc_id, "text": chunk_text})
        
        if not new_chunks:
            return

        self.collection.add(
            ids=[c['chunk_id'] for c in new_chunks],
            documents=[c['text'] for c in new_chunks],
            metadatas=[{'doc_id': c['doc_id']} for c in new_chunks]
        )
        self.chunks.extend(new_chunks)
        self._reindex_bm25()

    def _reindex_bm25(self):
        def tok(s: str) -> List[str]:
            return re.findall(r"[\w']+", s.lower())
        
        tokenized_chunks = [tok(c['text']) for c in self.chunks]
        if tokenized_chunks:
            self.bm25 = BM25Okapi(tokenized_chunks)

    def search(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        # 1. Sparse Search (BM25)
        bm25_results = []
        if self.bm25:
            qtok = re.findall(r"[\w']+", query.lower())
            scores = self.bm25.get_scores(qtok)
            top_n_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
            bm25_results = [(self.chunks[i]['chunk_id'], rank) for rank, i in enumerate(top_n_indices)]

        # 2. Dense Search (ChromaDB)
        dense_results_raw = self.collection.query(query_texts=[query], n_results=k)
        dense_results = [(chunk_id, rank) for rank, chunk_id in enumerate(dense_results_raw['ids'][0])]

        # 3. RRF Merge
        merged_ids = self._rrf_merge([bm25_results, dense_results])
        
        # 4. Get unique chunks by ID
        unique_chunks = {c['chunk_id']: c for c in self.chunks}
        final_chunks = [unique_chunks[id] for id in merged_ids if id in unique_chunks][:k]
        
        return final_chunks

    def _rrf_merge(self, ranklists: List[List[Tuple[str, int]]], const_k=60) -> List[str]:
        scores = {}
        for lst in ranklists:
            for doc_id, r in lst:
                scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (const_k + (r + 1))
        return [doc for doc, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)]

    def list_docs(self) -> List[Dict[str, Any]]:
        return [{"doc_id": doc_id, "text_preview": text[:100] + "...", "text_length": len(text)} for doc_id, text in self.docs.items()]

    def delete_doc(self, doc_id: str) -> bool:
        chunks_to_delete = [c['chunk_id'] for c in self.chunks if c['doc_id'] == doc_id]
        if not chunks_to_delete:
            return False
        
        self.collection.delete(ids=chunks_to_delete)
        self.chunks = [c for c in self.chunks if c['doc_id'] != doc_id]
        if doc_id in self.docs:
            del self.docs[doc_id]
        
        self._reindex_bm25()
        return True
