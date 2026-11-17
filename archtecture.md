================================================================================
                    END-TO-END RAG ARCHITECTURE SPECIFICATION
================================================================================
System Architecture: React.js + Node.js (Gateway) + FastAPI (AI Engine)
Retrieval Engine   : Hybrid (ChromaDB Vector + BM25) + Cross-Encoder Reranker
LLM Inference      : Groq API / Local Ollama (Streaming SSE)
Evaluation         : RAGAS Framework

--------------------------------------------------------------------------------
LAYER 1: USER REQUEST & FILE HANDLING (REACT.JS FRONTEND)
--------------------------------------------------------------------------------
- Component Role : Frontend Execution & Interaction Layer.
- User Action    : User drags and drops large files (PDFs/Text documents up to 500-1000+ pages).
- Client Logic   : 
  1. Client-side validation verifies file extension (.pdf, .txt) and size limits.
  2. Constructs a multipart payload using the HTML5 FormData API to trigger upload.
- Real-time Comms: 
  1. Establishes a WebSocket connection with the backend immediately upon upload initiation.
  2. Listens for streaming status frames to update the real-time UI progress bar 
     (e.g., "20% Text Extracted...", "60% Vectors Created...").

--------------------------------------------------------------------------------
LAYER 2: API GATEWAY & SECURITY LAYER (NODE.JS + EXPRESS)
--------------------------------------------------------------------------------
- Component Role : Gateway, Router & Session Manager.
- Authentication : Verifies the incoming HTTP request header using JWT (JSON Web Tokens).
- Storage & Audit: 
  1. Saves the raw uploaded file temporarily in a secure disk buffer directory.
  2. Generates an entry in SQL/MongoDB with schema: { file_id, user_id, status: "pending" }.
- Backend Handoff: Proxies the multipart payload to the internal FastAPI AI Engine via high-speed asynchronous HTTP/REST endpoints.

--------------------------------------------------------------------------------
STEP 1: ULTRA-FAST FILE PARSING & INGESTION (FASTAPI + PYMUPDF)
--------------------------------------------------------------------------------
- Component Role : Data Extraction Phase.
- Core Engine    : PyMuPDF (fitz C/C++ native engine bindings).
- Execution Flow : 
  1. FastAPI receives the byte stream in memory.
  2. Native C-bindings parse and convert 1000+ pages into structured raw plaintext.
- Performance    : Replaces pure Python loops with C-binary operations, completing full text extraction in 1–2 seconds.

--------------------------------------------------------------------------------
STEP 2: BACKGROUND TASK ORCHESTRATION (CELERY + REDIS)
--------------------------------------------------------------------------------
- Component Role : Asynchronous Non-Blocking Worker Layer.
- Task Queuing   : FastAPI offloads heavy compute workloads into a Celery Task Queue to keep the main web thread non-blocking.
- State Sync     : 
  1. Redis Cache manages worker task states and logs intermediate progress metrics.
  2. Node.js Gateway polls Redis state updates and emits them via WebSockets to the React UI.
  3. Prevents browser UI freezing or HTTP gateway request timeouts.

--------------------------------------------------------------------------------
STEP 3: PARALLEL CHUNKING & SEMANTIC STRUCTURING
--------------------------------------------------------------------------------
- Component Role : Data Segmentation Phase.
- Tooling        : RecursiveCharacterTextSplitter with Python Multiprocessing workers.
- Segmentation   : Extracted text is distributed across available multi-core CPUs and split into discrete 1000-character chunks.
- Context Overlap: Applies a 200-character sliding window overlap between adjacent chunks to prevent loss of semantic context across chunk boundaries.

--------------------------------------------------------------------------------
STEP 4: LOCAL VECTOR EMBEDDINGS GENERATION
--------------------------------------------------------------------------------
- Component Role : Feature Representation Phase.
- Model          : HuggingFace sentence-transformers (`BAAI/bge-small-en-v1.5`).
- Execution Flow : Batches of 1000 chunks are vectorized in parallel on CPU/RAM.
- System Design  : 
  1. 100% free open-source model (~130MB footprint) running locally with zero API key dependencies.
  2. High-precision semantic vector outputs stored locally.

--------------------------------------------------------------------------------
STEP 5: PERSISTENT INDEXING & MD5 CACHE CHECK
--------------------------------------------------------------------------------
- Component Role : Vector Storage & Zero-Delay Retrieval Phase.
- Database       : Persistent local ChromaDB instance utilizing HNSW (Hierarchical Navigable Small World) indexing.
- MD5 Deduplication: 
  1. Generates an MD5 checksum hash of the uploaded document immediately upon upload.
  2. Searches ChromaDB for matching existing hash keys.
  3. Cache Hit  : Skips Steps 1–4 entirely and loads pre-existing vector indexes instantly (0-second delay).
  4. Cache Miss : Executes full ingestion pipeline and stores persistent vector indexes.

--------------------------------------------------------------------------------
STEP 6: HYBRID SEARCH RETRIEVAL (ONLINE QUERYING)
--------------------------------------------------------------------------------
- Component Role : Candidate Retrieval Phase.
- Trigger Flow   : User submits a query in React Chat UI -> Node.js Gateway -> FastAPI AI Engine.
- Dual Pipeline  : 
  1. Dense Retrieval (ChromaDB): Executes cosine similarity vector search for high-level semantic meaning.
  2. Sparse Retrieval (BM25 Engine): Executes keyword matching for exact alphanumeric codes, proper names, and dates.
- Aggregation    : Merges and deduplicates candidate outputs into a Top-20 Candidate Chunk set.

--------------------------------------------------------------------------------
STEP 7: LOCAL PRECISION FILTERING & RE-RANKING
--------------------------------------------------------------------------------
- Component Role : Noise Elimination & Precision Phase.
- Model          : `cross-encoder/ms-marco-MiniLM-L-6-v2` (Local HuggingFace Cross-Encoder).
- Execution Flow : Evaluates query-chunk pairs simultaneously through a deep self-attention cross-encoder network.
- Precision Output: Filters out background noise from the Top-20 candidate set, passing ONLY the Top-3 highest-scoring, mathematically verified context chunks to the LLM.

--------------------------------------------------------------------------------
STEP 8: GUARDRAILED GENERATION & RESPONSE STREAMING
--------------------------------------------------------------------------------
- Component Role : Zero-Hallucination Inference Phase.
- LLM Engines    : Groq API (`llama-3.3-70b-versatile` / `llama3-8b-8192`) OR Local Ollama (`Llama-3 8B` / `Mistral 7B`).
- Guardrail Prompting: Enforces strict operational system instructions:
  - System must generate answers based SOLELY on the provided Top-3 context chunks.
  - If context is missing or inadequate, system MUST respond: "Mujhe answer book me nahi mila."
- Streaming Comms: Emits response via Server-Sent Events (SSE) token-by-token (FastAPI -> Node.js -> React UI) for real-time response rendering.

--------------------------------------------------------------------------------
STEP 9: SYSTEM EVALUATION PIPELINE (RAGAS TESTING)
--------------------------------------------------------------------------------
- Component Role : Automated Quality & Accuracy Assurance Phase.
- Framework      : RAGAS (Retrieval Augmented Generation Assessment).
- Metrics Benchmark:
  1. Faithfulness Score (Target: 1.0)      : Verifies generated output contains zero hallucinated facts.
  2. Answer Relevance Score (Target: 1.0)  : Verifies answer directly addresses user query intent.
  3. Context Precision Score (Target: 1.0) : Confirms Reranker successfully isolated pure noise-free context chunks.
================================================================================