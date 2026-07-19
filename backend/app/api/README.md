# 🌐 API Routing Layer

> [!TIP]
> The `api` module exposes the internal application logic as HTTP RESTful endpoints via FastAPI. 

## 🎯 Purpose and Responsibilities

This directory is strictly responsible for handling HTTP requests, sanitizing payload inputs, structuring JSON responses, and defining the Swagger/OpenAPI documentation schema. **No complex business logic or LLM prompting should exist here.**

## 📄 Endpoints

| Router | File | Purpose |
|--------|------|---------|
| **`/documents/upload`** | `documents.py` | Accepts `multipart/form-data` PDF uploads. Invokes the `DocumentService` to ingest and index the file. |
| **`/chat`** | `chat.py` | Accepts a JSON payload containing the user's question and an optional filename. Streams the query to the RAG service. |
| **`/cleanup`** | `cleanup.py` | Triggers the `CleanupService` to purge stale database entries and sync local storage with Qdrant. |
| **`/health`** | `health.py` | Standard ping endpoint for load balancers and container orchestration (Kubernetes/Docker). |
| **`/stats`** | `stats.py` | Exposes metrics like total documents, index sizes, and DB status. |

## ⚙️ Request Validation

FastAPI relies on Pydantic models (located in `backend/app/models/`) to strictly validate incoming requests. If a user sends malformed data to `/chat`, FastAPI natively intercepts it and returns a `422 Unprocessable Entity` before the request ever reaches the internal Python logic.
