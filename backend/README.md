# RATAN Backend (Developed by COEP)

This directory contains the core intelligence, processing, and API layer of the RATAN platform. It is designed to be highly scalable, asynchronous, and strictly secure for enterprise industrial environments.

## 🛠️ Technology Stack
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Language**: Python 3.10+
- **Primary Database**: SQLite (Local) / TiDB MySQL (Production)
- **Vector Database**: [Qdrant](https://qdrant.tech/)
- **Object Storage**: [Backblaze B2](https://www.backblaze.com/b2/cloud-storage.html)
- **LLM Orchestration**: [LangChain](https://python.langchain.com/)
- **Primary Inference**: Groq (Llama 3)
- **Fallback Inference**: Google Gemini

## 🛡️ Enterprise Security & Multi-Tenancy
- **Cryptographic Tenant Isolation**: All endpoints strictly derive `org_id`, `plant_id`, and `role` from the stateless JWT. User-supplied tenant IDs are actively rejected.
- **Vector Payload Bounding**: Qdrant vector queries are intercepted and bounded by the authenticated user's `org_id` at the lowest service level, completely preventing cross-tenant vector retrieval.
- **RBAC Strict Enforcement**: Tenant Admins are logically cordoned from SuperAdmin platform-wide analytics and API routes.
- **Secure IDOR Protection**: Document retrieval, vector chunk retrieval, chat histories, and maintenance tasks all validate organizational ownership before proceeding.

## 🧠 Core Systems

### 1. Retrieval-Augmented Generation (RAG)
Our RAG implementation is built for deterministic accuracy:
- Documents are chunked contextually, preserving engineering schemas and tables.
- Vector embeddings are generated using high-dimensional models.
- Retrieval leverages Qdrant with Maximal Marginal Relevance (MMR) and strict tenant-metadata filtering.
- Citations are built dynamically, ensuring that the frontend can pinpoint the exact document and page number for every AI claim.

### 2. Knowledge Graph Extraction
During document processing, an NLP pipeline identifies entities (Organizations, Tools, Parameters, Equipment) and relationships. This is stored and serialized into a format that the frontend Force-Directed Graph can visualize in real-time.

### 3. Document Lifecycle
Files are uploaded, hashed (SHA-256 for deduplication), and stored immutably in Backblaze B2. Processing occurs asynchronously:
- PDF Text Extraction
- Markdown Conversion (for tabular data)
- Chunking & Embedding
- Graph Extraction

### 4. Smart Database Translation
The backend utilizes a smart SQLAlchemy configuration that can dynamically switch between SQLite (development) and TiDB MySQL (production) while automatically handling dialect differences.

## 📁 Directory Structure
- `/app`
  - `/api`: FastAPI route handlers (Auth, Chat, Documents, Dashboard, Graph).
  - `/core`: Security, dependencies, and configuration (`config.py`).
  - `/db`: SQLAlchemy models and connection instances.
  - `/rag`: LangChain integrations, prompt building, and Qdrant client management.
  - `/services`: Business logic (Document Service, Auth Service).
- `main.py`: The application entry point.

## 🚀 Running Locally
1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure `.env` variables (refer to root README for required keys).
4. Start the server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
The Swagger UI API documentation will be available at `http://localhost:8000/docs`.
