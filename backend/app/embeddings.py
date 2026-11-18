from typing import List
import numpy as np
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class LocalEmbeddingEngine:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LocalEmbeddingEngine, cls).__new__(cls)
        return cls._instance

    @property
    def model(self):
        if self._model is None:
            logger.info(f"Loading Hugging Face embedding model: {settings.EMBEDDING_MODEL_NAME}...")
            import os
            if settings.HF_TOKEN:
                os.environ["HF_TOKEN"] = settings.HF_TOKEN
                os.environ["HUGGINGFACE_HUB_TOKEN"] = settings.HF_TOKEN
            from sentence_transformers import SentenceTransformer
            # Authenticated Hugging Face model loaded onto local CPU/RAM with ultra-low memory footprint (~80MB)
            self._model = SentenceTransformer(
                settings.EMBEDDING_MODEL_NAME,
                device="cpu",
                token=settings.HF_TOKEN if settings.HF_TOKEN else None
            )
            logger.info(f"Successfully loaded {settings.EMBEDDING_MODEL_NAME} from Hugging Face.")
        return self._model

    def embed_documents(self, texts: List[str], batch_size: int = 64) -> List[List[float]]:
        """Vectorize document chunks in batches."""
        if not texts:
            return []
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        """
        Vectorize user search query.
        BGE models benefit from instruction prefix for queries to maximize retrieval precision.
        """
        if "bge" in settings.EMBEDDING_MODEL_NAME.lower():
            query_text = f"Represent this sentence for searching relevant passages: {query}"
        else:
            query_text = query
        embedding = self.model.encode(
            [query_text],
            show_progress_bar=False,
            normalize_embeddings=True
        )[0]
        return embedding.tolist()

# Global singleton
embedding_engine = LocalEmbeddingEngine()
