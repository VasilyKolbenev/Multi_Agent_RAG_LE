import os, re
from typing import List, Tuple, Optional, Set, Dict, Any
from rank_bm25 import BM25Okapi

DOCS_DIR = os.environ.get("DOCS_DIR", "data/docs")

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

class Corpus:
    def __init__(self):
        self.docs: List[Tuple[str, str]] = []  # (doc_id, text)
        self.bm25 = None
        self.tokenized: List[List[str]] = []

    def load_folder(self, folder: str = DOCS_DIR):
        import glob
        self.docs.clear()
        for fp in glob.glob(os.path.join(folder, "*")):
            txt = _read_text(fp)
            if not txt.strip():
                continue
            doc_id = os.path.basename(fp)
            self.docs.append((doc_id, txt))
        self._reindex()

    def ingest_text(self, doc_id: str, text: str):
        self.docs.append((doc_id, text))
        self._reindex()

    def ingest_folder(self, folder: str):
        import glob
        for fp in glob.glob(os.path.join(folder, "*")):
            txt = _read_text(fp)
            if not txt.strip():
                continue
            doc_id = os.path.basename(fp)
            self.docs.append((doc_id, txt))
        self._reindex()

    def _reindex(self):
        def tok(s: str) -> List[str]:
            return re.findall(r"[\w']+", s.lower())
        self.tokenized = [tok(t) for _, t in self.docs]
        self.bm25 = BM25Okapi(self.tokenized) if self.tokenized else None

    def search(self, query: str, k: int = 5, allowed_docs: Optional[Set[str]] = None) -> List[Tuple[str, str, float]]:
        if not self.bm25:
            return []
        import numpy as np
        qtok = re.findall(r"[\w']+", query.lower())
        scores = self.bm25.get_scores(qtok)
        idx = np.argsort(scores)[::-1]
        out = []
        for i in idx:
            if scores[i] <= 0:
                break
            doc_id, text = self.docs[i]
            if allowed_docs is not None and doc_id not in allowed_docs:
                continue
            out.append((doc_id, text, float(scores[i])))
            if len(out) >= k:
                break
        return out

    def list_docs(self) -> List[Dict[str, Any]]:
        """Возвращает список загруженных документов с метаданными."""
        return [
            {"doc_id": doc_id, "text_preview": text[:100] + "...", "text_length": len(text)}
            for doc_id, text in self.docs
        ]

    def delete_doc(self, doc_id: str) -> bool:
        """Удаляет документ по его ID."""
        initial_len = len(self.docs)
        self.docs = [doc for doc in self.docs if doc[0] != doc_id]
        if len(self.docs) < initial_len:
            self._reindex()
            return True
        return False
