import os, json
from typing import Dict, Set, List

DATA_DIR = os.environ.get("DATA_DIR", "data")
GRAPH_PATH = os.path.join(DATA_DIR, "graph_index.json")

class GraphIndex:
    def __init__(self):
        self.entity_to_docs: Dict[str, Set[str]] = {}
        self._load()

    def _load(self):
        if os.path.exists(GRAPH_PATH):
            try:
                data = json.load(open(GRAPH_PATH, "r", encoding="utf-8"))
                self.entity_to_docs = {k: set(v) for k, v in data.items()}
            except Exception:
                self.entity_to_docs = {}

    def _save(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        data = {k: sorted(list(v)) for k, v in self.entity_to_docs.items()}
        json.dump(data, open(GRAPH_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    @staticmethod
    def _norm(val: str) -> str:
        return (val or "").strip().lower()

    def update_from_items(self, doc_id: str, items: List[dict]):
        changed = False
        for it in items:
            ent = self._norm(it.get("text") or it.get("value") or "")
            if not ent:
                continue
            s = self.entity_to_docs.setdefault(ent, set())
            if doc_id not in s:
                s.add(doc_id); changed = True
        if changed:
            self._save()

    def filter_docs(self, entities: List[str]) -> Set[str]:
        docs: Set[str] = set()
        for e in entities:
            s = self.entity_to_docs.get(self._norm(e))
            if s:
                docs |= s
        return docs
    
    def get_all_entities_with_stats(self) -> List[Dict[str, any]]:
        """Возвращает все сущности с статистикой по документам."""
        result = []
        
        for entity_text, doc_ids in self.entity_to_docs.items():
            if entity_text and doc_ids:
                result.append({
                    "text": entity_text.title(),  # Красиво форматируем
                    "class": "entity",  # Базовый тип
                    "doc_count": len(doc_ids)
                })
        
        # Сортируем по популярности
        result.sort(key=lambda x: x["doc_count"], reverse=True)
        return result