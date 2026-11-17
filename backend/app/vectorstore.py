import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
import json
import logging
from app.config import settings
from app.embeddings import embedding_engine

logger = logging.getLogger(__name__)

class ChromaVectorStore:
    _instance = None
    _client = None
    _collection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChromaVectorStore, cls).__new__(cls)
            cls._instance._init_db()
        return cls._instance

    def _init_db(self):
        persist_dir = str(settings.CHROMA_PERSIST_DIR)
        logger.info(f"Initializing persistent ChromaDB at {persist_dir}...")
        self._client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        # HNSW indexing with cosine space for ultra-fast vector retrieval
        self._collection = self._client.get_or_create_collection(
            name="document_chunks",
            metadata={"hnsw:space": "cosine"}
        )
        logger.info("ChromaDB persistent collection 'document_chunks' ready.")

    @property
    def collection(self):
        return self._collection

    def check_hash_exists(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """
        Check if document with identical MD5 hash already exists in ChromaDB.
        Returns document metadata if found (Instant 0-second cache hit), else None.
        """
        results = self._collection.get(
            where={"file_hash": file_hash},
            limit=1,
            include=["metadatas"]
        )
        if results and results["ids"] and len(results["ids"]) > 0:
            meta = results["metadatas"][0]
            # Count total chunks for this doc
            total_chunks = len(self._collection.get(where={"file_hash": file_hash})["ids"])
            return {
                "doc_id": meta.get("doc_id"),
                "filename": meta.get("filename"),
                "file_hash": file_hash,
                "total_chunks": total_chunks,
                "total_pages": meta.get("total_pages", 1)
            }
        return None

    def add_chunks(
        self,
        chunks: List[Dict[str, Any]],
        file_hash: str,
        total_pages: int,
        progress_callback=None
    ):
        """
        Batches vector embeddings and indexes chunks with HNSW metadata into ChromaDB.
        """
        if not chunks:
            return

        batch_size = 100
        total = len(chunks)

        for i in range(0, total, batch_size):
            batch = chunks[i:i + batch_size]
            ids = [c["chunk_id"] for c in batch]
            documents = [c["text"] for c in batch]
            metadatas = [
                {
                    "doc_id": c["doc_id"],
                    "filename": c["filename"],
                    "page_number": c["page_number"],
                    "chunk_seq": c["chunk_seq"],
                    "file_hash": file_hash,
                    "total_pages": total_pages
                }
                for c in batch
            ]

            # Vectorize batch locally
            embeddings = embedding_engine.embed_documents(documents)

            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )

            if progress_callback:
                pct = min(100, int(((i + len(batch)) / total) * 100))
                progress_callback(pct, f"Indexed {min(i + len(batch), total)} of {total} chunks...")

        logger.info(f"Successfully indexed {total} chunks into ChromaDB.")

    def dense_search(
        self,
        query: str,
        n_results: int = settings.TOP_K_DENSE,
        doc_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Dense vector similarity search using BGE query embedding and ChromaDB HNSW cosine index.
        """
        query_embedding = embedding_engine.embed_query(query)
        where_filter = {"doc_id": doc_id} if doc_id else None

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        candidates = []
        if results and results["ids"] and len(results["ids"][0]) > 0:
            for idx in range(len(results["ids"][0])):
                doc_text = results["documents"][0][idx]
                meta = results["metadatas"][0][idx]
                dist = results["distances"][0][idx]
                # Cosine distance in Chroma: similarity = 1 - distance
                sim_score = max(0.0, 1.0 - dist)

                candidates.append({
                    "chunk_id": results["ids"][0][idx],
                    "doc_id": meta.get("doc_id", ""),
                    "filename": meta.get("filename", ""),
                    "page_number": meta.get("page_number", 1),
                    "text": doc_text,
                    "score": float(sim_score),
                    "source": "dense_vector"
                })

        return candidates

    def get_all_documents(self) -> List[Dict[str, Any]]:
        """List all unique documents ingested into ChromaDB."""
        all_data = self._collection.get(include=["metadatas"])
        if not all_data or not all_data["metadatas"]:
            return []

        docs_map = {}
        for meta in all_data["metadatas"]:
            doc_id = meta.get("doc_id")
            if doc_id and doc_id not in docs_map:
                docs_map[doc_id] = {
                    "doc_id": doc_id,
                    "filename": meta.get("filename", "Unknown"),
                    "file_hash": meta.get("file_hash", ""),
                    "total_pages": meta.get("total_pages", 1),
                    "chunk_count": 0
                }
            if doc_id in docs_map:
                docs_map[doc_id]["chunk_count"] += 1

        return list(docs_map.values())

    def get_all_chunks_for_doc(self, doc_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve chunks from ChromaDB for BM25 sparse keyword indexing."""
        where_filter = {"doc_id": doc_id} if doc_id else None
        results = self._collection.get(
            where=where_filter,
            include=["documents", "metadatas"]
        )
        chunks = []
        if results and results["ids"]:
            for i, chunk_id in enumerate(results["ids"]):
                chunks.append({
                    "chunk_id": chunk_id,
                    "doc_id": results["metadatas"][i].get("doc_id", ""),
                    "filename": results["metadatas"][i].get("filename", ""),
                    "page_number": results["metadatas"][i].get("page_number", 1),
                    "text": results["documents"][i]
                })
        return chunks

# Global singleton
vector_store = ChromaVectorStore()
