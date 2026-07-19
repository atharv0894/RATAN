# 🚦 Orchestration Services

> [!IMPORTANT]
> The `services` module acts as the "glue" that binds the API layer to the backend processing layers (Storage, Database, RAG, and NLP).

## 🎯 Purpose and Responsibilities

Services encapsulate complex workflows that require coordinating multiple different components. By keeping this logic in `services/`, the API routers stay clean and the architecture remains highly modular.

## 📄 Key Services

| Service | Description |
|---------|-------------|
| `document_service.py` | Manages the full lifecycle of a PDF. Orchestrates storing the file (StorageService), chunking and vectorizing it (RAG Engine), updating its status (SQLite DB), and cleaning up. |
| `cleanup_service.py` | An automated maintenance service. Finds documents stuck in a "Processing" state, purges dangling vectors from Qdrant, and synchronizes the local database to prevent ghost files. |
| `dependencies.py` | Implements FastAPI's Dependency Injection pattern. Exposes instances of `DocumentService` and `RAGService` to the API routes safely, managing initialization and cache lifespans. |

## ⚙️ Lifecycle Example: `process_and_index()`
When a document is uploaded, `document_service.py` handles:
1. Checking for exact duplicates using SHA-256 hashes.
2. Saving the initial metadata to SQLite with a `Processing` status.
3. Invoking the Chunking and Vectorizing algorithms.
4. Catching any errors, marking the document as `Failed`.
5. On success, marking it as `Indexed` and logging the computation time.
