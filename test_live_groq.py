import asyncio
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(BASE_DIR))

from app.parser import parse_document
from app.chunker import chunk_pages_data
from app.vectorstore import vector_store
from app.hybrid_retriever import hybrid_retriever
from app.reranker import reranker
from app.llm import llm_client

async def test_live_query():
    pdf_path = Path(r"d:\ai projects\chatbot\test_documents\Project_Quantum_Aegis_Technical_Manual.pdf")
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    print("Parsing PDF...")
    pages, total_pages, file_hash = parse_document(file_bytes, pdf_path.name)
    print(f"Parsed {total_pages} pages.")

    doc_id = "test_aegis_manual"
    chunks = chunk_pages_data(pages, doc_id, pdf_path.name)
    print(f"Created {len(chunks)} chunks.")

    print("Indexing in ChromaDB...")
    vector_store.add_chunks(chunks, file_hash, total_pages)
    hybrid_retriever.update_bm25_index(doc_id)

    # Test Question 1: In-document technical query
    q1 = "Who is the Chief Architect of Project Quantum Aegis and where is it deployed?"
    print(f"\n--- Testing Live Question 1: '{q1}' ---")
    candidates = hybrid_retriever.retrieve(q1, doc_id)
    top_3 = reranker.rerank(q1, candidates, 3)

    print("Groq LLM Streaming Response:")
    async for token in llm_client.stream_answer(q1, top_3):
        print(token, end="", flush=True)
    print("\n")

    # Test Question 2: Absence Rule (Out of document)
    q2 = "What is the secret recipe for chocolate pizza in this document?"
    print(f"\n--- Testing Absence Rule Question 2: '{q2}' ---")
    candidates2 = hybrid_retriever.retrieve(q2, doc_id)
    top_3_q2 = reranker.rerank(q2, candidates2, 3)

    print("Groq LLM Streaming Response:")
    async for token in llm_client.stream_answer(q2, top_3_q2):
        print(token, end="", flush=True)
    print("\n")

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(test_live_query())
