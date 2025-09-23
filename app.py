from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import os

app = FastAPI(title="MultiAgent-RAG Pro")

# CORS
origins = [
    "https://vasilykolbenev.github.io",
    "https://vasilykolbenev.github.io/Multi_Agent_RAG_LE",
    "https://*.vercel.app",
    "http://localhost:3000",
    "http://localhost:5173",
    "null",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Простое хранилище
documents_storage = {}

@app.get("/")
def root():
    return {"message": "MultiAgent-RAG API на Vercel", "status": "working"}

@app.get("/health")
def health():
    return {"ok": True, "model": "gpt-5-mini", "platform": "vercel"}

@app.get("/documents")
def get_documents():
    return list(documents_storage.values())

@app.post("/ingest")
async def ingest_unified(files: List[UploadFile] = File(None), text: str = Form(None)):
    results = []
    
    if text and text.strip():
        doc_id = f"text_{len(documents_storage)}"
        documents_storage[doc_id] = {
            "doc_id": doc_id,
            "content": text,
            "type": "text"
        }
        results.append({"type": "text", "doc_id": doc_id})
    
    return {"ok": True, "results": results, "count": len(results)}

@app.get("/ask/agentic")
async def ask_agentic(q: str):
    # Простой поиск
    relevant_docs = []
    query_lower = q.lower()
    
    for doc in documents_storage.values():
        if any(word in doc["content"].lower() for word in query_lower.split()):
            relevant_docs.append({
                "doc_id": doc["doc_id"],
                "content": doc["content"][:300],
                "score": 0.8
            })
    
    if relevant_docs:
        answer = f"На основе найденных документов отвечаю на вопрос: '{q}'. Найдено {len(relevant_docs)} релевантных документов."
    else:
        answer = f"По вопросу '{q}' документы не найдены. Загрузите документы через /ingest."
    
    return {
        "answer": answer,
        "sources": relevant_docs[:3],
        "agentic_metadata": {"iterations_used": 1}
    }

# Vercel handler
handler = app