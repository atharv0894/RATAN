# RATAN: Industrial Knowledge Intelligence Platform

![RATAN Architecture](https://img.shields.io/badge/Architecture-RAG-blue) ![Python](https://img.shields.io/badge/Python-3.11%2B-green) ![FastAPI](https://img.shields.io/badge/FastAPI-0.109.2-teal) ![Status](https://img.shields.io/badge/Status-Production--Ready-success)

## 📖 Project Overview
**RATAN** (Retrieval-Augmented Technical Analytics Network) is an enterprise-grade Industrial Knowledge Intelligence Platform. 

### Problem Statement
Manufacturing and industrial enterprises possess vast repositories of technical manuals, annual reports, troubleshooting guides, and SOPs. This data is often stored in legacy formats, fragmented across multiple languages (English, Hindi, Marathi), and locked within dense, multi-column PDFs. Accessing precise technical information quickly during critical operational downtime is a significant bottleneck.

### Motivation
To bridge the gap between static industrial documentation and dynamic, intelligent retrieval. Engineers and operators need a zero-shot, cross-lingual system that can read a manual in Marathi and answer complex troubleshooting queries in Hindi seamlessly.

### Objectives
- Create a highly accurate Retrieval-Augmented Generation (RAG) system.
- Support legacy industrial PDFs, including complex tables and financial reports.
- Enable native cross-lingual semantic search (English ↔ Hindi ↔ Marathi).
- Guarantee hallucination resistance by strictly enforcing document-grounded citations.

### Features
- **Semantic Chunking:** Context-aware slicing of dense industrial PDFs using `BAAI/bge-m3`.
- **Hybrid Search Engine:** `Qdrant` vector database combined with entity-based metadata filtering.
- **Resilient Generation:** Primary generation via `GPT-OSS 120B` with intelligent auto-failover to `Gemini 2.5 Flash`.
- **Advanced Table Extraction:** Preserves spatial and relational contexts of deep financial tables.
- **Multilingual Native Retrieval:** Query natively across Hindi, Marathi, and English.
- **Transparent Citations:** Every generated fact is traced back to the exact chunk, page, and document.

---

## 🏗 Architecture Diagram

```mermaid
flowchart TD
    User([User Client]) -->|Upload PDF| API[FastAPI Backend]
    User -->|Ask Question| API
    
    subgraph Ingestion Pipeline
        API -->|Parse| Loader[PDF Plumber Loader]
        Loader -->|Split| Chunker[Semantic Chunker]
        Chunker -->|Vectorize| Embed[BAAI/bge-m3 Embedder]
        Embed -->|Store| DB[(Qdrant Vector DB)]
        Embed -->|Save File| Storage[Local Storage]
    end
    
    subgraph Retrieval Pipeline
        API -->|Extract| Entity[Entity Extractor]
        Entity -->|Filter Metadata| DB
        API -->|Embed Query| Embed
        Embed -->|Search| DB
        DB -->|MMR Reranking| Retriever[Retrieval Service]
    end
    
    subgraph Generation Pipeline
        Retriever -->|Construct Context| Prompt[Prompt Builder]
        Prompt -->|Primary LLM| Groq[GPT-OSS 120B]
        Groq -- Rate Limit / Outage --> Gemini[Gemini 2.5 Flash]
        Groq -->|Answer & Citations| API
        Gemini -->|Answer & Citations| API
    end
```

### Sequence Flow: Chat Pipeline

```mermaid
sequenceDiagram
    actor User
    participant API as FastAPI Router
    participant Retriever as Retrieval Service
    participant Qdrant as Vector DB
    participant LLM as GPT-OSS (Groq)
    participant Fallback as Gemini (Google)

    User->>API: POST /chat {question, filename}
    API->>Retriever: generate_answer(query)
    Retriever->>LLM: decompose_query(query)
    LLM-->>Retriever: [sub_queries]
    
    loop For each sub_query
        Retriever->>Qdrant: similarity_search()
        Qdrant-->>Retriever: Top K Chunks
    end
    
    Retriever->>Retriever: MMR Reranking & Deduplication
    Retriever->>LLM: invoke(context + original_query)
    
    alt If Groq Rate Limited (HTTP 429)
        LLM-->>Retriever: 429 Too Many Requests
        Retriever->>Retriever: Automatic Backoff (max_retries=5)
        Retriever->>LLM: retry invoke()
    else If Groq Offline (HTTP 503)
        LLM-->>Retriever: Exception
        Retriever->>Fallback: invoke(context + original_query)
        Fallback-->>Retriever: Generated Answer
    end
    
    LLM-->>Retriever: Generated Answer (JSON)
    Retriever-->>API: {answer, citations}
    API-->>User: JSON Response
```

---

## 📂 Folder Structure

```text
.
├── backend/
│   ├── app/                    # Core Application Logic
│   │   ├── api/                # FastAPI Routers (Endpoints)
│   │   ├── database/           # SQLite Connections
│   │   ├── entity/             # NLP Entity Extraction Rules
│   │   ├── models/             # Pydantic Schemas
│   │   ├── rag/                # RAG Core (Chunking, Embedding, LLM)
│   │   ├── services/           # Orchestration & Cleanup Services
│   │   └── storage/            # File Management Interfaces
│   ├── storage/uploads/        # Local PDF storage volume
│   ├── .env                    # Environment variables
│   ├── requirements.txt        # Python dependencies
│   └── main.py                 # FastAPI Application Entrypoint
```

### Responsibilities
* **`app/api/`**: Exposes HTTP endpoints. Sanitizes inputs and formats outputs.
* **`app/rag/`**: The brain of the system. Handles semantic chunking, embedding generation, MMR reranking, and LLM communication.
* **`app/services/`**: Binds the API layer to the internal RAG and Storage layers. Manages lifecycle events (e.g., document uploading, cleanup).
* **`app/storage/`**: Abstracts the file system. Currently hard-locked to Local Storage for production stability.

---

## 🛠 Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend Framework** | `FastAPI` | High-performance asynchronous API server. |
| **Embeddings** | `BAAI/bge-m3` | State-of-the-art multilingual embedding model (1024 dims). |
| **Vector DB** | `Qdrant` | High-speed cloud vector similarity search. |
| **Primary LLM** | `openai/gpt-oss-120b` (via Groq) | Fast, highly accurate reasoning and generation. |
| **Fallback LLM** | `gemini-2.5-flash` (via Google) | Redundant generation pipeline for disaster recovery. |
| **Relational DB** | `SQLite` | Tracks document metadata and processing statuses. |
| **File Parsing** | `pdfplumber` | Precise spatial PDF extraction (tables and text). |

---

## 🔌 API Documentation

### 1. Upload Document
* **Route:** `/documents/upload`
* **Method:** `POST`
* **Description:** Uploads a PDF file, chunks it, vectorizes the text, and stores it in Qdrant.
* **Request Body:** `multipart/form-data` containing the `file`.
* **Response:**
  ```json
  {
    "document_id": "uuid-string",
    "filename": "manual.pdf",
    "status": "Ready",
    "message": "Document processed successfully"
  }
  ```

### 2. Chat Query
* **Route:** `/chat`
* **Method:** `POST`
* **Description:** Queries the RAG system to generate an answer based on the ingested documents.
* **Request Body:**
  ```json
  {
    "question": "What is the operating temperature?",
    "filename": "manual.pdf"
  }
  ```
  *(Note: `filename` is optional. If omitted, it defaults to a global semantic search across all indexed PDFs).*
* **Response:**
  ```json
  {
    "answer": "The operating temperature is 45C.",
    "citations": [
      {
        "text": "...operating temperature is 45C...",
        "source": "manual.pdf",
        "page_no": 12
      }
    ],
    "entities": []
  }
  ```

### 3. Cleanup System
* **Route:** `/cleanup`
* **Method:** `POST`
* **Description:** Forces a backend synchronization. Purges failed documents, cleans up dangling vector indexes, and resolves stale SQLite states.
* **Response:** `{"status": "success", "message": "Cleanup completed."}`

---

## 🌊 Pipeline Data Flows

### 📥 Upload Pipeline
1. **Receive:** FastAPI accepts the PDF bytes.
2. **Save:** `LocalStorage` saves the PDF to disk.
3. **Parse:** `DocumentLoader` extracts text and spatial data using `pdfplumber`.
4. **Chunk:** `Chunker` divides text into semantically complete, overlapping chunks (preserving markdown tables).
5. **Embed:** `EmbeddingService` converts chunks to 1024-dimension vectors via `BAAI/bge-m3`.
6. **Store:** `Qdrant` stores vectors and associated metadata (Source, Page, Chunk ID).

### 🤖 Chat Pipeline
1. **Decompose:** Complex user questions are broken down into simpler sub-queries.
2. **Retrieve:** Each sub-query fetches the Top K chunks from Qdrant via Cosine Similarity.
3. **Rerank:** Maximal Marginal Relevance (MMR) removes duplicate context and maximizes diversity.
4. **Prompt Construction:** Chunks are injected into a strict system prompt demanding JSON outputs and explicit citations.
5. **Generation:** Groq LLM streams the answer. If Groq hits a `429`, the system auto-retries. If Groq fails entirely, the system auto-routes to Gemini.

---

## 🛡 Storage Architecture

* **Cloud Storage (`Backblaze B2`):** Acts as the primary cold-storage volume for raw PDFs. Ensures high durability and accessibility across distributed nodes.
* **Local Cache (`backend/storage/uploads/`):** Acts as a temporary ephemeral cache for file processing before uploading to B2.
* **Vector Storage (`Qdrant`):** Manages the dense vector embeddings and metadata indexing.
* **SQLite (`ratan_registry.db`):** Maintains the source of truth for UI client status polling (`Processing`, `Ready`, `Failed`).

### Error Handling Protocols
| Error Scenario | System Response |
|----------------|-----------------|
| **Invalid/Corrupt PDF** | Caught during `pdfplumber` initialization. Fails gracefully. Status marked as `Failed`. |
| **Legacy Fonts (Kruti Dev)** | Embeddings process raw CID characters. LLM safely reports: *"The provided document does not specify this."* (Requires future OCR integration). |
| **Groq Rate Limit (429)** | Native exponential backoff triggers. Thread sleeps and retries seamlessly up to 5 times. |
| **Groq Outage (500/503)** | Exception caught. Traffic routed to Fallback `Gemini` client. |
| **Missing API Keys** | Fast-fails on startup via strict `os.environ` validation in dependencies. |

---

## ⚙️ Environment Variables

| Variable | Purpose | Required | Example |
|----------|---------|----------|---------|
| `GROQ_API_KEY` | Primary LLM Authentication | Yes | `gsk_abc123...` |
| `GOOGLE_API_KEY` | Fallback LLM Auth | Yes | `AIzaSy_...` |
| `QDRANT_URL` | Vector DB Cluster Endpoint | Yes | `https://xyz.qdrant.io` |
| `QDRANT_API_KEY` | Vector DB Auth Token | Yes | `eyJhbG...` |
| `STORAGE_PROVIDER` | Toggle storage ('local' or 'b2') | No (Defaults to local) | `b2` |
| `B2_KEY_ID` | Backblaze B2 Key ID | Yes (if b2) | `005f4c4d...` |
| `B2_APPLICATION_KEY` | Backblaze B2 App Key | Yes (if b2) | `K005E64e...` |
| `B2_BUCKET_NAME` | Backblaze B2 Bucket Name | Yes (if b2) | `RATANAI` |

---

## 🚀 Installation Guide

### Local Development Setup

1. **Clone the Repository**
   ```bash
   git clone <repo-url>
   cd "Ei ai hackton"/backend
   ```

2. **Create a Virtual Environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   Edit the `.env` file and insert your valid API keys (Groq, Google, Qdrant).

5. **Run the Backend**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.1 --port 8000
   ```
   *The Swagger UI will be available at http://127.0.0.1:8000/docs*

---

## 🔮 Future Improvements & Limitations
1. **OCR Preprocessing:** Legacy Hindi PDFs (encoded with non-Unicode fonts like Kruti Dev) cannot currently be parsed by `pdfplumber`. Integration with `Tesseract` or `Surya-OCR` is required for total legacy ingestion capability.
2. **Frontend Integration:** The backend architecture is fully production-hardened. The next phase is mapping the provided API contracts to a React/Next.js frontend.
3. **Session Memory:** Implementing a conversational buffer (e.g., `Redis` chat history) to allow multi-turn reasoning without requiring massive context window injections.

---
*Generated by the Principal AI Architect Team.*
