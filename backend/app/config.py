import os
# Windows OpenBLAS memory stability
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from pathlib import Path
from pydantic_settings import BaseSettings

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent

class Settings(BaseSettings):
    # API & Host Settings
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    PROJECT_NAME: str = "Ultra-Fast Fact-Grounding RAG Engine"
    
    # LLM Settings (Groq)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    
    # Hugging Face Configuration
    HF_TOKEN: str = ""
    
    # Storage Paths
    DATA_DIR: Path = BASE_DIR / "data"
    CHROMA_PERSIST_DIR: Path = BASE_DIR / "data" / "chroma"
    CACHE_DIR: Path = BASE_DIR / "data" / "cache"
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    
    # Background Task Broker
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Embedding & Reranker Local Models (0% Cost, runs locally on CPU/RAM)
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"
    RERANKER_MODEL_NAME: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    # Chunking Configuration
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # Retrieval Configuration
    TOP_K_DENSE: int = 10
    TOP_K_SPARSE: int = 10
    TOP_K_RERANK: int = 3
    
    # Strict Guardrail System Prompt
    STRICT_PROMPT_TEMPLATE: str = """SYSTEM INSTRUCTION:
You are an extremely strict, factual Document Analysis Engine. You must answer questions using ONLY the verified CONTEXT provided below.

STRICT LAWS:
1. TRUTHFULNESS: Your answer must be strictly derived from the provided CONTEXT. Do not use any external pre-trained knowledge or facts.
2. ABSENCE RULE: If the answer is not directly stated in the CONTEXT, you MUST reply with EXACTLY: "Mujhe is ka jawab uploaded document me nahi mila."
3. NO HALLUCINATION: Do not synthesize assumptions or educated guesses. If context is partial, answer only what is explicitly written.
4. CITATION: Mention the relevant section or quote from the context if available.
5. TEMPORAL & ENTITY PRECISION: Pay meticulous attention to dates, years, versions, and numeric figures. If the user asks about a specific timeframe or year (e.g. 2024, 2029) or a specific version/model code, and the context only mentions an adjacent or different timeframe (e.g. 2023, 2026) or version, NEVER substitute or guess. Treat the requested timeframe or entity as absent and reply with the ABSENCE RULE.

[CONTEXT START]
{context}
[CONTEXT END]

USER QUESTION: {query}
ANSWER:"""

    class Config:
        env_file = [
            str(ROOT_DIR / ".env"),
            str(BASE_DIR / ".env")
        ]
        extra = "allow"

# Global settings instance
settings = Settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
