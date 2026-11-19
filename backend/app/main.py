import os
import uuid
import json
import time
import asyncio
import logging
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from sse_starlette.sse import EventSourceResponse

from app.config import settings
from app.schemas import UploadResponse, QueryRequest, QueryResponse, DocumentChunk, DocumentInfo
from app.parser import calculate_md5
from app.embeddings import embedding_engine
from app.vectorstore import vector_store
from app.hybrid_retriever import hybrid_retriever
from app.reranker import reranker
from app.llm import llm_client
from app.celery_app import (
    execute_ingestion_pipeline,
    task_progress_state,
    update_task_progress,
    celery_app
)

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("rag_fastapi")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Ultra-fast zero-hallucination RAG Document Chatbot Engine"
)

# Enable CORS for local Vite dev server and Node gateway
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing RAG AI Engine: Fast port binding mode...")
    try:
        hybrid_retriever.update_bm25_index()
    except Exception as e:
        logger.warning(f"Initial BM25 index notice: {e}")
    logger.info("RAG Engine started successfully. Port bound.")

    # Background pre-warm ONNX model so user uploads never wait for initial download
    async def prewarm_onnx():
        try:
            logger.info("Pre-warming ONNX model in background...")
            _ = embedding_engine.model
            logger.info("ONNX model pre-warmed and cached.")
        except Exception as err:
            logger.warning(f"Background prewarm notice: {err}")
    asyncio.create_task(prewarm_onnx())

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Ultra-Fast Fact-Grounding RAG Engine",
        "docs": "/docs",
        "health": "/api/health"
    }

@app.get("/api/session")
async def get_session():
    return {"token": "session-active", "status": "authenticated"}

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "service": "RAG Core AI Backend",
        "embedding_model": settings.EMBEDDING_MODEL_NAME,
        "reranker_model": settings.RERANKER_MODEL_NAME,
        "groq_model": settings.GROQ_MODEL,
        "groq_configured": bool(settings.GROQ_API_KEY and settings.GROQ_API_KEY != "your_groq_api_key_here")
    }

@app.post("/api/upload", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Handle document upload with MD5 cache verification and background ingestion.
    - If MD5 hash exists in ChromaDB: instant 0-second cache hit!
    - If new: runs asynchronous ingestion pipeline and emits progress.
    """
    filename = file.filename or "uploaded_document"
    contents = await file.read()
    
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Step 5: MD5 Deduplication Check
    file_hash = calculate_md5(contents)
    cache_hit = vector_store.check_hash_exists(file_hash)

    if cache_hit:
        doc_id = cache_hit["doc_id"]
        logger.info(f"MD5 Cache Hit for {filename} (Hash: {file_hash}). Skipping ingestion.")
        # Ensure BM25 has this doc indexed
        hybrid_retriever.update_bm25_index(doc_id)
        return UploadResponse(
            task_id=f"cached_{file_hash}",
            doc_id=doc_id,
            filename=filename,
            cached=True,
            status="completed",
            total_pages=cache_hit.get("total_pages", 1),
            total_chunks=cache_hit.get("total_chunks", 0),
            message="Document already indexed in ChromaDB. Loaded instantly (0s delay)."
        )

    # Cache Miss: Generate new doc_id and task_id
    doc_id = f"doc_{uuid.uuid4().hex[:8]}"
    task_id = f"task_{uuid.uuid4().hex[:12]}"

    # Save to disk buffer
    file_path = settings.UPLOAD_DIR / f"{doc_id}_{filename}"
    with open(file_path, "wb") as f:
        f.write(contents)

    # Initialize task progress
    update_task_progress(task_id, doc_id, filename, "queued", 5, "Upload received, starting background worker...")

    # Offload to Background Task
    background_tasks.add_task(
        execute_ingestion_pipeline,
        file_bytes=contents,
        filename=filename,
        doc_id=doc_id,
        task_id=task_id,
        file_hash=file_hash
    )

    return UploadResponse(
        task_id=task_id,
        doc_id=doc_id,
        filename=filename,
        cached=False,
        status="processing",
        total_pages=0,
        total_chunks=0,
        message="Upload accepted. Background worker processing document..."
    )

@app.get("/api/progress/{task_id}")
async def get_progress_stream(request: Request, task_id: str):
    """
    Server-Sent Events (SSE) streaming endpoint for real-time progress bar (0% - 100%).
    """
    async def event_generator():
        last_progress = -1
        while True:
            if await request.is_disconnected():
                break

            state = task_progress_state.get(task_id)
            if state:
                if state["progress"] != last_progress:
                    last_progress = state["progress"]
                    yield {
                        "event": "progress",
                        "data": json.dumps(state)
                    }
                else:
                    # Keep-alive heartbeat ping to prevent cloud proxy disconnects
                    yield {"comment": "ping"}
                if state["status"] in ["completed", "error"]:
                    break
            else:
                yield {"comment": "waiting"}
                # If cached task
                if task_id.startswith("cached_"):
                    yield {
                        "event": "progress",
                        "data": json.dumps({
                            "task_id": task_id,
                            "status": "completed",
                            "progress": 100,
                            "message": "Loaded instantly from ChromaDB cache."
                        })
                    }
                    break
            await asyncio.sleep(0.4)

    return EventSourceResponse(event_generator())

@app.get("/api/progress/{task_id}/status")
async def get_task_progress_status(task_id: str):
    """Direct polling fallback for progress bar."""
    state = task_progress_state.get(task_id)
    if not state:
        if task_id.startswith("cached_"):
            return {"task_id": task_id, "status": "completed", "progress": 100, "message": "Loaded instantly from ChromaDB cache."}
        return {"task_id": task_id, "status": "processing", "progress": 50, "message": "Indexing document..."}
    return state

@app.post("/api/query")
async def query_document(request: QueryRequest):
    """
    Online Querying Pipeline:
    1. Hybrid Search: Dense Vector (ChromaDB) + Sparse (BM25) -> Top 20 Candidates
    2. Precision Reranking: Cross-Encoder -> Top 3 verified chunks
    3. LLM Response: Stream tokens via SSE using Groq API and strict guardrail prompt
    """
    query_text = request.query.strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    clean_q = query_text.lower()
    is_greeting = any(clean_q.startswith(g) or clean_q == g for g in [
        "hy", "hi", "hello", "hey", "salam", "assalam", "halo", "kaise ho", "kya haal", "good morning", "good evening", "who are you"
    ])
    has_docs = bool(vector_store.get_all_documents())

    if is_greeting or not has_docs:
        greeting_text = (
            "Hello! I am DocuMind AI, your verified enterprise document assistant. "
            "Please upload a PDF, TXT, or Markdown document on the left panel to begin asking questions, "
            "and I will analyze its facts with zero hallucination!"
            if not has_docs else
            "Hello! I am ready to answer any questions strictly based on your uploaded document. How can I help you today?"
        )
        async def sse_greeting():
            yield {"event": "sources", "data": json.dumps({"sources": [], "retrieval_time": 0.0})}
            yield {"event": "token", "data": json.dumps({"token": greeting_text})}
            yield {"event": "done", "data": json.dumps({"total_time": 0.05})}
        return EventSourceResponse(sse_greeting())

    start_time = time.time()

    try:
        # Step 6: Hybrid Search Retrieval (Top 20 candidates)
        candidates = hybrid_retriever.retrieve(query=query_text, doc_id=request.doc_id)

        # Step 7: Cross-Encoder Precision Reranking (Top 3 chunks)
        top_3_chunks = reranker.rerank(query=query_text, candidates=candidates, top_k=settings.TOP_K_RERANK)
    except Exception as e:
        logger.error(f"Error during retrieval/reranking: {e}", exc_info=True)
        top_3_chunks = []

    retrieval_latency = time.time() - start_time
    logger.info(f"Retrieval + Rerank took {retrieval_latency:.3f}s. Top chunks: {len(top_3_chunks)}")

    # Format sources for client citation drawer
    formatted_sources = [
        {
            "chunk_id": c.get("chunk_id"),
            "doc_id": c.get("doc_id"),
            "filename": c.get("filename"),
            "page_number": c.get("page_number", 1),
            "text": c.get("text"),
            "score": round(c.get("rerank_score", c.get("score", 0.0)), 4),
            "source_type": c.get("source", "hybrid")
        }
        for c in top_3_chunks
    ]

    async def sse_chat_generator():
        # First event: deliver verified source citations
        yield {
            "event": "sources",
            "data": json.dumps({
                "sources": formatted_sources,
                "retrieval_time": round(retrieval_latency, 3)
            })
        }

        # Step 8: Stream LLM tokens
        try:
            async for token in llm_client.stream_answer(query_text, top_3_chunks):
                yield {
                    "event": "token",
                    "data": json.dumps({"token": token})
                }
        except Exception as e:
            logger.error(f"Error streaming LLM tokens: {e}", exc_info=True)
            yield {
                "event": "token",
                "data": json.dumps({"token": f"\n\n[Error generating answer: {str(e)}]"})
            }

        # Final event: Done
        total_time = round(time.time() - start_time, 3)
        yield {
            "event": "done",
            "data": json.dumps({"total_time": total_time})
        }

    return EventSourceResponse(sse_chat_generator())

@app.get("/api/documents")
async def list_documents():
    """List all ingested documents and stats."""
    docs = vector_store.get_all_documents()
    return {"documents": docs, "total": len(docs)}

@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document and its chunks from ChromaDB."""
    try:
        vector_store.collection.delete(where={"doc_id": doc_id})
        hybrid_retriever.update_bm25_index()
        return {"status": "success", "message": f"Document {doc_id} deleted."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
