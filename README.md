# RATAN: Retrieval-Augmented Technology for Asset Networks

Welcome to **RATAN**, an Enterprise Industrial Knowledge Intelligence Platform.

RATAN transforms fragmented industrial knowledge—like operational manuals, maintenance logs, and safety procedures—into an intelligent, highly searchable, and interactive knowledge graph powered by cutting-edge Retrieval-Augmented Generation (RAG).

## Architecture

RATAN is designed for production readiness, leveraging a modern AI tech stack:
- **FastAPI**: Asynchronous, high-performance web framework.
- **Qdrant**: Scalable vector database for ultra-fast semantic search.
- **SQLite**: Local metadata store for relational state tracking (RBAC, Tenants, Document versions).
- **Backblaze B2**: Cost-effective S3-compatible cloud storage for raw document archiving.
- **LLMs (Groq & Gemini)**: Fast inference APIs for intelligent conversational retrieval and intent classification.

## Key Features

1. **Enterprise Document Processing Pipeline**
   - Page-aware semantic chunking.
   - Hash-based deduplication preventing redundant vector DB inserts.
   - Universal format support (`.pdf`, `.docx`, `.txt`, `.md`, `.csv`).
   
2. **Dynamic Search Engine (Strategy Pattern)**
   - **SimilaritySearch**: Ultra-fast vector matches.
   - **MMRSearch**: Maximal Marginal Relevance for diverse context generation.
   - **HybridSearch**: Keyword and semantic blending for complex procedural queries.
   - **MetadataSearch**: Strict boolean filtering (Tenant, Plant, Department).

3. **Enterprise Security (RBAC & JWT)**
   - Hardened `access` and `refresh` token flow.
   - Strict Tenant Isolation enforcing `organization_id` bounds at the Qdrant filter level.
   - Role-Based Access Control (`Admin`, `Plant Manager`, etc.) for all API routes.

4. **Production Observability & CI/CD**
   - Comprehensive `/health` diagnostics (Memory, DB state, LLM status).
   - Global Request Latency & Audit Logging.
   - Full GitHub Actions CI/CD Pipeline (Ruff, Mypy, Bandit, Pytest).

## Quick Start

### 1. Environment Setup

Copy `.env.example` to `.env` inside the `backend` directory and fill in your keys:
```bash
cp backend/.env.example backend/.env
```

### 2. Run the Backend (Local)

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. API Documentation
Visit `http://localhost:8000/docs` to view the interactive Swagger OpenAPI documentation.

## Deployment
RATAN is configured for seamless deployment on containerized platforms (Docker, Render, AWS ECS). The CI pipeline ensures code quality prior to merges.
