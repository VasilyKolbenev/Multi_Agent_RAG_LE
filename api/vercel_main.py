import os
import sys
import json
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Простая версия для Vercel без тяжелых зависимостей
app = FastAPI(title="MultiAgent-RAG Pro - Vercel")

# CORS настройки
origins = [
    "https://vasilykolbenev.github.io",
    "https://vasilykolbenev.github.io/Multi_Agent_RAG_LE",
    "https://multiagent-rag-api.vercel.app",
    "https://*.vercel.app",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost",
    "null",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Простое хранилище в памяти для документов
documents_storage = {}

@app.get("/health")
def health():
    return {"ok": True, "model": os.getenv("LLM_MODEL", "gpt-5-mini")}

@app.get("/documents")
def get_documents():
    return list(documents_storage.values())

@app.post("/ingest")
async def ingest_unified(files: List[UploadFile] = File(None), text: str = Form(None)):
    """Упрощенная версия для Vercel"""
    results = []
    
    if text and text.strip():
        doc_id = f"text_{len(documents_storage)}"
        documents_storage[doc_id] = {
            "doc_id": doc_id,
            "content": text,
            "type": "text"
        }
        results.append({"type": "text", "doc_id": doc_id})
    
    if files:
        for file in files:
            doc_id = f"file_{file.filename}_{len(documents_storage)}"
            content = await file.read()
            try:
                text_content = content.decode('utf-8')
            except:
                text_content = f"Binary file: {file.filename}"
            
            documents_storage[doc_id] = {
                "doc_id": doc_id,
                "content": text_content,
                "type": "file",
                "filename": file.filename
            }
            results.append({"type": "file", "filename": file.filename})
    
    return {"ok": True, "results": results, "count": len(results)}

@app.get("/ask/agentic")
async def ask_agentic(q: str, max_iterations: int = 5):
    """Упрощенная версия для демонстрации"""
    try:
        # Простой поиск по документам
        relevant_docs = []
        query_lower = q.lower()
        
        for doc in documents_storage.values():
            if any(word in doc["content"].lower() for word in query_lower.split()):
                relevant_docs.append({
                    "doc_id": doc["doc_id"],
                    "content": doc["content"][:500],
                    "score": 0.8
                })
        
        # Простой ответ
        if relevant_docs:
            answer = f"На основе найденных документов ({len(relevant_docs)} шт.), могу сказать следующее по вашему вопросу: '{q}'\n\nНайденная информация указывает на релевантные данные в загруженных документах. Для получения более точного ответа с использованием GPT-5 mini, необходимо настроить полную интеграцию с OpenAI API."
        else:
            answer = f"По вашему вопросу '{q}' не найдено релевантных документов в загруженной базе знаний. Пожалуйста, загрузите соответствующие документы для получения точного ответа."
        
        return {
            "answer": answer,
            "sources": relevant_docs[:3],
            "agentic_metadata": {
                "iterations_used": 1,
                "confidence": 0.7
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"message": f"Agentic RAG error: {e}"}
        )

@app.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    if doc_id in documents_storage:
        del documents_storage[doc_id]
        return {"status": "ok", "message": f"Document {doc_id} deleted."}
    else:
        return JSONResponse(
            {"status": "error", "message": f"Document {doc_id} not found."}, 
            status_code=404
        )

# Vercel handler - экспортируем app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
