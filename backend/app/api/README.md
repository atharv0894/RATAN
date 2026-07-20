# API Layer (`app/api/`)

This directory defines the FastAPI routers and endpoints. It strictly handles HTTP request validation and response mapping, delegating all complex processing to the `services/` layer.

## Endpoints
- `auth.py`: JWT-based Registration, Login, and User Profile.
- `chat.py`: Intelligent RAG conversational endpoint with integrated chat history.
- `documents.py`: File uploading, list retrieval, soft-deletion, and restore operations.
- `entities.py`: Extracts and lists industrial entities (Plants, Equipment, Persons) found across documents.
- `health.py`: Diagnostics probing SQLite, Qdrant, Memory, and Disk usage.
- `stats.py`: Aggregated global platform statistics.
- `cleanup.py`: Job scheduler for physically deleting soft-deleted files and stale vectors.

## Standards
- All responses are wrapped in `APISuccessResponse` or `APIPaginatedResponse` (`app/api/responses.py`).
- Security is strictly enforced per-route via `Depends(RequireRole([...]))`.
