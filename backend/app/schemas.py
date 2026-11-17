from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class DocumentChunk(BaseModel):
    chunk_id: str
    doc_id: str
    filename: str
    page_number: int
    text: str
    score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class UploadResponse(BaseModel):
    task_id: str
    doc_id: str
    filename: str
    cached: bool
    status: str
    total_pages: Optional[int] = 0
    total_chunks: Optional[int] = 0
    message: str

class ProgressUpdate(BaseModel):
    task_id: str
    doc_id: str
    filename: str
    status: str # "parsing", "chunking", "embedding", "indexing", "completed", "error"
    progress: int # 0 to 100
    message: str

class QueryRequest(BaseModel):
    query: str = Field(..., description="User query question")
    doc_id: Optional[str] = Field(None, description="Optional doc_id filter, or search across all docs")

class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[DocumentChunk]
    latency_seconds: float

class DocumentInfo(BaseModel):
    doc_id: str
    filename: str
    file_hash: str
    total_pages: int
    total_chunks: int
    created_at: str
