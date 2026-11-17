from typing import List, Dict, Any, Optional
import re
import logging
from rank_bm25 import BM25Okapi
from app.config import settings
from app.vectorstore import vector_store

logger = logging.getLogger(__name__)

def normalize_query(query: str) -> str:
    """Normalize common typos, plural forms, and punctuation in user queries."""
    typo_map = {
        r"\bpromt\b": "prompt",
        r"\bpromts\b": "prompts",
        r"\barchtecture\b": "architecture",
        r"\brequriment\b": "requirement",
        r"\brequirment\b": "requirement",
        r"\brequirments\b": "requirements",
        r"\bspec\b": "specification",
        r"\bspecs\b": "specifications",
    }
    q = query.strip()
    for pattern, replacement in typo_map.items():
        q = re.sub(pattern, replacement, q, flags=re.IGNORECASE)
    return q

class HybridRetriever:
    def __init__(self):
        self.bm25_indices: Dict[str, BM25Okapi] = {}
        self.bm25_chunks: Dict[str, List[Dict[str, Any]]] = {}

    def _tokenize(self, text: str) -> List[str]:
        """
        Compound alphanumeric tokenizer for BM25.
        Captures compound identifiers (e.g. 'v1.2', 'aegis-9', 'iso-9001'),
        individual words, and automatically collapses letter-spaced headers (e.g. 'P R O M P T' -> 'prompt').
        """
        text_lower = text.lower()
        # Collapse spaced uppercase / lowercase letters (e.g. 'p r o m p t' -> 'prompt')
        collapsed = re.sub(r'(?<=\b[a-z0-9])\s+(?=[a-z0-9]\b)', '', text_lower)
        
        compounds = re.findall(r"[a-z0-9]+(?:[\.\-_][a-z0-9]+)+", text_lower)
        words = re.findall(r"\w+", text_lower)
        collapsed_words = re.findall(r"\w+", collapsed)
        return list(set(words + compounds + collapsed_words))

    def update_bm25_index(self, doc_id: Optional[str] = None):
        """Build or refresh BM25 inverted index from ChromaDB documents."""
        key = doc_id or "all"
        chunks = vector_store.get_all_chunks_for_doc(doc_id)
        if not chunks:
            return

        corpus_tokens = [self._tokenize(c["text"]) for c in chunks]
        self.bm25_indices[key] = BM25Okapi(corpus_tokens)
        self.bm25_chunks[key] = chunks
        logger.info(f"Built BM25 index for '{key}' with {len(chunks)} chunks.")

    def sparse_search(
        self,
        query: str,
        n_results: int = settings.TOP_K_SPARSE,
        doc_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Sparse BM25 search for exact alphanumeric keywords, terms, and codes."""
        key = doc_id or "all"
        if key not in self.bm25_indices:
            self.update_bm25_index(doc_id)

        bm25 = self.bm25_indices.get(key)
        chunks = self.bm25_chunks.get(key)

        if not bm25 or not chunks:
            return []

        tokens = self._tokenize(query)
        if not tokens:
            return []

        doc_scores = bm25.get_scores(tokens)
        # Get top-N score indices
        top_indices = sorted(range(len(doc_scores)), key=lambda i: doc_scores[i], reverse=True)[:n_results]

        sparse_candidates = []
        for idx in top_indices:
            score = float(doc_scores[idx])
            if score > 0:  # Only include if there is keyword match
                chunk = chunks[idx].copy()
                chunk["score"] = score
                chunk["source"] = "sparse_bm25"
                sparse_candidates.append(chunk)

        return sparse_candidates

    def retrieve(
        self,
        query: str,
        doc_id: Optional[str] = None,
        top_dense: int = settings.TOP_K_DENSE,
        top_sparse: int = settings.TOP_K_SPARSE
    ) -> List[Dict[str, Any]]:
        """
        Hybrid retrieval combining Dense Vector Search (ChromaDB) and Sparse BM25 Keyword Search.
        Merges, normalizes, deduplicates into a unified Top 20 candidate pool.
        """
        clean_query = normalize_query(query)

        # 1. Dense Vector Retrieval (Top 10)
        dense_results = vector_store.dense_search(query=clean_query, n_results=top_dense, doc_id=doc_id)

        # 2. Sparse BM25 Retrieval (Top 10)
        sparse_results = self.sparse_search(query=clean_query, n_results=top_sparse, doc_id=doc_id)

        # 3. Deduplicate and merge candidates
        seen_ids = set()
        merged_candidates = []

        # Add dense results first (captures semantic context)
        for chunk in dense_results:
            if chunk["chunk_id"] not in seen_ids:
                seen_ids.add(chunk["chunk_id"])
                merged_candidates.append(chunk)

        # Add sparse results (captures exact codes, dates, names)
        for chunk in sparse_results:
            if chunk["chunk_id"] not in seen_ids:
                seen_ids.add(chunk["chunk_id"])
                merged_candidates.append(chunk)

        logger.info(
            f"Hybrid retrieval retrieved {len(dense_results)} dense and {len(sparse_results)} sparse chunks. "
            f"Total unique candidates: {len(merged_candidates)}"
        )
        return merged_candidates

# Global singleton
hybrid_retriever = HybridRetriever()
