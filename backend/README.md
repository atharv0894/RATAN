# RATAN Backend Service

This is the core backend service for the RATAN (Retrieval-Augmented Technology for Asset Networks) platform. It provides a robust, scalable, and secure API for processing industrial documents and executing intelligent RAG queries.

## Technology Stack
- **Framework**: FastAPI (Python 3.11+)
- **Metadata Database**: SQLite (Normalized V2 Schema)
- **Vector Database**: Qdrant Cloud
- **Object Storage**: Backblaze B2 (S3 Compatible)
- **Authentication**: PyJWT & Passlib (Bcrypt)
- **Testing**: Pytest (90%+ Coverage target)

## Project Structure
```text
app/
├── api/          # FastAPI Routers (auth, chat, documents, etc.)
├── database/     # SQLite configuration and V2 Schema Definition
├── entity/       # Entity Extraction pipelines
├── exceptions.py # Global custom exception handlers
├── main.py       # Application entrypoint & Middleware
├── models/       # Pydantic core schemas
├── rag/          # Core AI logic (Vector Store, Parsers, Strategy Engine, Reranker)
├── services/     # Business logic layer (Auth, Documents, Dependencies)
└── storage/      # Local and Cloud (Backblaze) storage providers
```

## Setup & Execution

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Server**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Running Tests**
   ```bash
   pytest --cov=app tests/
   ```

## Security Posture
- **JWT Authorization**: Enforced across all state-mutating endpoints.
- **RBAC**: Protected by `RequireRole` decorators.
- **Tenant Isolation**: Deeply integrated into SQL queries and Qdrant `WHERE` clauses to prevent horizontal privilege escalation.
- **Audit Logging**: Tracks every request execution via middleware.
