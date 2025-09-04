import os, uuid, json
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from .retrieval import HybridCorpus
from .graph_index import GraphIndex
from .agents import MultiAgent
from .storage import append_trace, read_traces
from .langx import run_extraction, stream_extraction
from .profiles import PROFILES

app = FastAPI(title="MultiAgent-RAG Pro")

# Настройка CORS для конкретных доменов
origins = [
    "https://vasilykolbenev.github.io",  # Ваш GitHub Pages
    "http://localhost:8001",           # Локальный сервер для тестов
    "http://localhost",                # На всякий случай
    "null",                            # Для локальных файлов (file://)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

corpus = HybridCorpus()
graph = GraphIndex()
agent = MultiAgent(corpus, graph)

@app.get("/health")
def health(): return {"ok": True, "model": os.getenv("LLM_MODEL","gpt-5-mini")}

@app.get("/profiles")
def profiles(): return PROFILES

@app.get("/traces")
def traces(): return read_traces()

@app.post("/ingest/text")
async def ingest_text(text: str = Form(...), doc_id: Optional[str] = Form(None)):
    """Принимает текст, генерирует ID, если он не предоставлен."""
    try:
        if not doc_id:
            # Генерируем простой doc_id на основе хэша текста
            import hashlib
            doc_id = f"doc_{hashlib.md5(text[:100].encode()).hexdigest()[:8]}"
            
        corpus.ingest_text(doc_id, text)
        append_trace({"type":"ingest", "doc_id":doc_id, "len":len(text)})
        return {"ok": True, "doc_id": doc_id}
    except Exception as e:
        print(f"ERROR in /ingest/text: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"message": "Internal Server Error during ingestion"})

@app.post("/ingest/files")
async def ingest_files(files: List[UploadFile] = File(...)):
    saved = []
    base = os.environ.get("DOCS_DIR", "data/docs"); os.makedirs(base, exist_ok=True)
    for f in files:
        fp = os.path.join(base, f.filename)
        with open(fp, "wb") as out: out.write(await f.read())
        saved.append(f.filename)
    corpus.load_folder(base)
    append_trace({"type":"ingest_files", "files":saved})
    return {"ok": True, "files": saved, "count": len(saved)}

@app.post("/ingest/folder")
async def ingest_folder(path: str = Form(...)):
    corpus.ingest_folder(path)
    append_trace({"type":"ingest_folder", "path": path})
    return {"ok": True}

@app.get("/search")
def search(q: str, k: int = 5, entities: Optional[str] = None):
    # Фильтрация по сущностям здесь больше не поддерживается напрямую,
    # так как поиск теперь гибридный. Можно добавить в будущем.
    res = corpus.search(q, k=k)
    return JSONResponse(res)

@app.get("/ask")
async def ask(q: str, k: int = 5, entities: Optional[str] = None):
    ents = [x.strip() for x in entities.split(",")] if entities else None
    append_trace({"type":"query", "q": q, "entities": ents})
    res = await agent.run(q, k=k, entities_filter=ents)
    append_trace({"type":"result", "q": q, "answer": res.get("answer","")[:200], "citations": res.get("citations", [])})
    return JSONResponse(res)

@app.get("/ask/stream")
async def ask_stream(q: str, k: int = 5, entities: Optional[str] = None):
    """Эндпоинт для потоковой передачи RAG-ответа."""
    ents = [x.strip() for x in entities.split(",")] if entities else None
    
    async def event_generator():
        try:
            async for event in agent.stream(q, k=k, entities_filter=ents):
                yield {
                    "event": "message",
                    "data": json.dumps(event)
                }
        except Exception as e:
            # Отправляем событие с ошибкой на фронтенд
            error_event = {"type": "error", "data": f"Произошла ошибка: {e}"}
            yield {
                "event": "message",
                "data": json.dumps(error_event)
            }
            # Также логируем ошибку на сервере
            print(f"Error during stream: {e}")

    return EventSourceResponse(
        event_generator(),
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/documents")
def get_documents():
    """Возвращает список всех загруженных документов."""
    return JSONResponse(corpus.list_docs())

@app.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    """Удаляет документ по его ID."""
    success = corpus.delete_doc(doc_id)
    if success:
        return JSONResponse({"status": "ok", "message": f"Document {doc_id} deleted."})
    else:
        return JSONResponse({"status": "error", "message": f"Document {doc_id} not found."}, status_code=404)

@app.post("/langextract/text")
async def langextract_text(task_prompt: str = Form(None), text: str = Form(...), doc_id: str = Form("extracted_doc")):
    try:
        out = run_extraction(text, prompt=task_prompt)
        graph.update_from_items(doc_id, out["items"])
        return JSONResponse(out)
    except Exception as e:
        print(f"ERROR in /langextract/text: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"message": "Internal Server Error during extraction"})

@app.get("/langextract/stream_text")
async def langextract_stream_text(text: str, task_prompt: Optional[str] = None, doc_id: str = "extracted_doc"):
    def gen():
        last = None
        for ev in stream_extraction(text, prompt=task_prompt):
            last = ev
            yield {"event": "message", "data": json.dumps(ev, ensure_ascii=False)}
        if last and isinstance(last, dict) and "result" in last:
            graph.update_from_items(doc_id, last["result"].get("items", []))
    return EventSourceResponse(gen())

@app.get("/extracts/{job_id}/viz.html")
async def get_viz(job_id: str):
    fp = os.path.join("data","extracts",job_id,"viz.html")
    if not os.path.exists(fp): return JSONResponse({"error":"not found"}, status_code=404)
    return FileResponse(fp, media_type="text/html")
