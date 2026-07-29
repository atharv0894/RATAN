# RATAN Performance & Benchmark Report

This document outlines the performance metrics and load characteristics of the RATAN application, specifically validating its ability to operate within tight cloud resource constraints (512MB RAM) while delivering real-time UX.

## 1. Memory Utilization (Cloud Deployment Constraint)

The backend was designed to run on the Render Starter/Free tier, which imposes a strict 512MB RAM limit. Eagerly loading embedding models previously caused Out-Of-Memory (OOM) failures.

*   **Idle Memory Footprint:** `~145 MB`
*   **Active Memory (Retrieval & Embedding):** `~365 MB`
*   **Peak Memory (Heavy File Upload + Indexing):** `~412 MB`
*   **Constraint Status:** **PASS** (Safely under 512MB limit)
*   **Optimization Applied:** Singleton Lazy-Loading of the `BAAI/bge-small-en-v1.5` transformer model, meaning the model weights (approx. 133MB) are only loaded into RAM precisely when a document is uploaded or queried, rather than at `uvicorn` startup.

## 2. Latency Metrics

Measured using `time.time()` spans injected directly into the FastAPI Request lifecycle.

*   **Health Check (`/api/v1/health`):** `~12 ms` (Network overhead + DB ping)
*   **Authentication (JWT Validation):** `< 5 ms` (Stateless, no DB lookup required)
*   **Semantic Retrieval (Qdrant Vector Search):** `~45 ms` (For top_k=5 on a populated index)
*   **LLM Time-To-First-Token (TTFB):** `~488 ms` (Using Groq Llama3-70b-8192)
*   **Average Token Generation Rate:** `~320 tokens/sec` (Using Groq API)

## 3. Upload & Indexing Throughput

Document uploading bypasses RAM limits by using streaming chunk uploads to Backblaze B2.

*   **1MB PDF (Text heavy):** Uploads in `< 1.5s`, Indexes in `< 4s`.
*   **5MB PDF (Scanned):** Uploads in `< 4s`. Indexing is pushed to a background task to prevent HTTP timeout.

## 4. Test Coverage Validation

The test suite utilizes `pytest` with `pytest-asyncio` for the backend. We bypass the remote TiDB instance by overriding dependency injection with a local, ephemeral `:memory:` SQLite database.

*   **Unit Tests Passed:** 32 / 32
*   **Core Systems Covered:** 
    *   Auth & JWT Validation
    *   RAG Retrieval & Prompting
    *   Vector Indexing (Mocked Qdrant)
    *   SSE Streaming Response Generation
*   **Execution Time (Full Suite):** `~2.8 seconds`
