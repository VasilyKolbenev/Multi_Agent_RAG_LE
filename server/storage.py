import json, time, os
from typing import Any, Dict, List
DATA_DIR = os.environ.get("DATA_DIR","data")
TRACE_FILE = os.path.join(DATA_DIR, "traces.jsonl")
os.makedirs(DATA_DIR, exist_ok=True)
def append_trace(event: Dict[str, Any]) -> None:
    event = dict({"ts": time.time()}, **event)
    with open(TRACE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
def read_traces() -> List[Dict[str, Any]]:
    if not os.path.exists(TRACE_FILE):
        return []
    return [json.loads(x) for x in open(TRACE_FILE,"r",encoding="utf-8").read().splitlines() if x.strip()]
