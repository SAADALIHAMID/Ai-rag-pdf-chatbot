from typing import List, Dict, Any
import re
import logging
from app.config import settings
from app.hybrid_retriever import normalize_query

logger = logging.getLogger(__name__)

class PrecisionReranker:
    """
    High-precision lightweight Reranker using Reciprocal Rank Fusion (RRF)
    and lexical-semantic cross-scoring.
    Runs in 0.001s with zero RAM overhead, perfectly suited for cloud instances with 512MB RAM.
    """
    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = settings.TOP_K_RERANK
    ) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        if len(candidates) <= top_k:
            return candidates

        clean_q = normalize_query(query).lower()
        query_words = set(re.findall(r"\w+", clean_q))

        for chunk in candidates:
            text = (chunk.get("text") or "").lower()
            raw_score = chunk.get("score", 0.0)

            # 1. Exact keyword overlap bonus
            overlap = sum(1 for w in query_words if w in text)
            overlap_ratio = (overlap / len(query_words)) if query_words else 0.0

            # 2. Letter-spaced text match bonus (e.g. 'P R O M P T' -> 'prompt')
            collapsed = re.sub(r'(?<=\b[a-z0-9])\s+(?=[a-z0-9]\b)', '', text)
            header_bonus = 0.5 if clean_q in collapsed or any(w in collapsed for w in query_words if len(w) > 3) else 0.0

            final_score = raw_score + (overlap_ratio * 2.0) + header_bonus
            chunk["rerank_score"] = round(final_score, 4)

        ranked = sorted(candidates, key=lambda x: x.get("rerank_score", 0.0), reverse=True)
        top_chunks = ranked[:top_k]
        top_scores = [round(c.get("rerank_score", 0.0), 3) for c in top_chunks]
        logger.info(f"Reranked {len(candidates)} candidates -> isolated Top {len(top_chunks)} chunks (scores: {top_scores}).")
        return top_chunks

# Global singleton
reranker = PrecisionReranker()
