from typing import List, Dict, Any
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class PrecisionReranker:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PrecisionReranker, cls).__new__(cls)
        return cls._instance

    @property
    def model(self):
        if self._model is None:
            logger.info(f"Loading Hugging Face Cross-Encoder reranker: {settings.RERANKER_MODEL_NAME}...")
            import os
            if settings.HF_TOKEN:
                os.environ["HF_TOKEN"] = settings.HF_TOKEN
                os.environ["HUGGINGFACE_HUB_TOKEN"] = settings.HF_TOKEN
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(
                settings.RERANKER_MODEL_NAME,
                model_kwargs={"token": settings.HF_TOKEN} if settings.HF_TOKEN else {}
            )
            logger.info(f"Loaded {settings.RERANKER_MODEL_NAME} from Hugging Face successfully.")
        return self._model

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = settings.TOP_K_RERANK
    ) -> List[Dict[str, Any]]:
        """
        Cross-Encoder precision reranking over Top-20 candidate chunks.
        Computes joint query-chunk cross-attention scores and extracts Top-3 exact chunks.
        """
        if not candidates:
            return []

        if len(candidates) <= top_k:
            return candidates

        import re
        from app.hybrid_retriever import normalize_query
        clean_q = normalize_query(query)

        # Prepare (clean_q, chunk_text) pairs for the cross-encoder
        # We collapse spaced letters (e.g. 'P R O M P T' -> 'PROMPT') so cross-attention catches matches
        pairs = []
        for c in candidates:
            chunk_text = c.get("text", "")
            collapsed_text = re.sub(r'(?<=\b[A-Za-z])\s+(?=[A-Za-z]\b)', '', chunk_text)
            # Combine original and collapsed for maximum cross-encoder sensitivity
            eval_text = f"{chunk_text}\n{collapsed_text}"
            pairs.append([clean_q, eval_text])

        # Compute cross-encoder relevance scores
        scores = self.model.predict(pairs)

        # Attach scores to candidate dicts
        for idx, score in enumerate(scores):
            candidates[idx]["rerank_score"] = float(score)

        # Sort candidates strictly by cross-encoder score descending
        ranked_candidates = sorted(candidates, key=lambda x: x.get("rerank_score", -999.0), reverse=True)

        top_chunks = ranked_candidates[:top_k]
        top_scores = [round(c.get("rerank_score", 0.0), 3) for c in top_chunks]
        logger.info(f"Reranked {len(candidates)} candidates -> isolated Top {len(top_chunks)} chunks (scores: {top_scores}).")
        return top_chunks

# Global singleton
reranker = PrecisionReranker()
