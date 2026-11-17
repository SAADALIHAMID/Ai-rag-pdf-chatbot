import os
import time
import logging
from typing import Dict, Any
from celery import Celery
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    "rag_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

# In-memory progress tracking fallback (for instant polling when Redis is optional or standalone)
task_progress_state: Dict[str, Dict[str, Any]] = {}

def update_task_progress(task_id: str, doc_id: str, filename: str, status: str, progress: int, message: str):
    """Update progress state in memory and emit logger info."""
    state = {
        "task_id": task_id,
        "doc_id": doc_id,
        "filename": filename,
        "status": status,
        "progress": progress,
        "message": message,
        "timestamp": time.time()
    }
    task_progress_state[task_id] = state
    logger.info(f"Task {task_id} [{progress}%]: {message}")

def execute_ingestion_pipeline(
    file_bytes: bytes,
    filename: str,
    doc_id: str,
    task_id: str,
    file_hash: str
) -> Dict[str, Any]:
    """
    Core synchronous/asynchronous ingestion execution logic.
    Steps:
    1. Parse (PyMuPDF) -> Sub-second C-level text extraction
    2. Chunk (RecursiveCharacterTextSplitter) -> 1000 char blocks, 200 overlap
    3. Embed & Index (BGE-small + ChromaDB HNSW)
    4. Build BM25 sparse index
    """
    from app.parser import parse_document
    from app.chunker import chunk_pages_data
    from app.vectorstore import vector_store
    from app.hybrid_retriever import hybrid_retriever

    try:
        # Step 1: Parse Document
        update_task_progress(task_id, doc_id, filename, "parsing", 15, "Parsing document with PyMuPDF...")
        pages_data, total_pages, _ = parse_document(file_bytes, filename)

        if not pages_data:
            update_task_progress(task_id, doc_id, filename, "error", 100, "No readable text found in document.")
            return {"status": "error", "message": "No text extracted"}

        # Step 2: Chunk Text
        update_task_progress(task_id, doc_id, filename, "chunking", 35, f"Structuring {total_pages} pages into 1000-char chunks...")
        chunks = chunk_pages_data(pages_data, doc_id, filename)
        total_chunks = len(chunks)

        # Step 3: Embed & Store in ChromaDB
        update_task_progress(task_id, doc_id, filename, "embedding", 50, f"Generating BGE embeddings for {total_chunks} chunks...")

        def on_embed_progress(pct: int, msg: str):
            # Scale 50% to 90%
            current_pct = 50 + int(pct * 0.40)
            update_task_progress(task_id, doc_id, filename, "indexing", current_pct, msg)

        vector_store.add_chunks(
            chunks=chunks,
            file_hash=file_hash,
            total_pages=total_pages,
            progress_callback=on_embed_progress
        )

        # Step 4: Build BM25 Index for Hybrid Retrieval
        update_task_progress(task_id, doc_id, filename, "indexing", 95, "Building BM25 sparse keyword index...")
        hybrid_retriever.update_bm25_index(doc_id)

        # Finished
        update_task_progress(
            task_id,
            doc_id,
            filename,
            "completed",
            100,
            f"Successfully indexed {total_pages} pages ({total_chunks} chunks)."
        )

        return {
            "status": "completed",
            "doc_id": doc_id,
            "filename": filename,
            "total_pages": total_pages,
            "total_chunks": total_chunks
        }

    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}", exc_info=True)
        update_task_progress(task_id, doc_id, filename, "error", 100, f"Failed: {str(e)}")
        return {"status": "error", "message": str(e)}

@celery_app.task(bind=True, name="process_document_task")
def process_document_task(self, file_path: str, filename: str, doc_id: str, file_hash: str):
    """Celery background worker task."""
    task_id = self.request.id
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        return execute_ingestion_pipeline(file_bytes, filename, doc_id, task_id, file_hash)
    finally:
        # Clean up temp file if needed
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
