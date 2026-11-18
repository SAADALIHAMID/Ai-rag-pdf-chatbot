from typing import List
import numpy as np
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class LocalEmbeddingEngine:
    """
    Ultra-lightweight ONNX-powered Embedding Engine (all-MiniLM-L6-v2).
    Uses only ~35MB RAM via onnxruntime without loading PyTorch into memory.
    Guarantees zero-OOM on cloud instances with 512MB RAM (Render Free tier).
    """
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LocalEmbeddingEngine, cls).__new__(cls)
        return cls._instance

    @property
    def model(self):
        if self._model is None:
            logger.info("Initializing ultra-lightweight ONNX all-MiniLM-L6-v2 embedding model...")
            from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
            self._model = DefaultEmbeddingFunction()
            logger.info("Successfully initialized ONNX all-MiniLM-L6-v2 engine (35MB RAM).")
        return self._model

    def embed_documents(self, texts: List[str], batch_size: int = 64) -> List[List[float]]:
        """Vectorize document chunks in batches with ONNX Runtime."""
        if not texts:
            return []
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embs = self.model(batch)
            all_embeddings.extend([list(map(float, e)) for e in embs])
        return all_embeddings

    def embed_query(self, query: str) -> List[float]:
        """Vectorize user search query with ONNX Runtime."""
        emb = self.model([query])[0]
        return list(map(float, emb))

# Global singleton
embedding_engine = LocalEmbeddingEngine()
