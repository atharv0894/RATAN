# 🛠️ Backend Environment Directory

This directory contains the entire Python backend for the RATAN Industrial Knowledge Intelligence Platform. 

It is designed as a highly scalable, asynchronous application using **FastAPI**. It handles everything from document ingestion (PDF chunking and embedding) to the complex Retrieval-Augmented Generation (RAG) pipeline via Qdrant and GPT-OSS.

## 🎯 Purpose
The `backend/` folder isolates all server-side logic, environment configuration, database state, and vector models away from the client-side/frontend code. 

## 📄 Key Files and Directories

| Item | Type | Description |
|------|------|-------------|
| `app/` | Directory | The core FastAPI application containing all routes, RAG logic, and services. |
| `storage/` | Directory | Local cache where incoming PDFs are securely buffered before being uploaded to Backblaze B2. |
| `chroma_db/` | Directory | Legacy/fallback local vector storage (currently superseded by Qdrant). |
| `test_data/` | Directory | Contains sample industrial PDFs for validation and QA stress testing. |
| `ratan_registry.db` | File | The SQLite database that tracks document metadata and processing statuses. |
| `requirements.txt` | File | The `pip` dependency list detailing all required packages (FastAPI, Langchain, etc.). |
| `.env` | File | Environment variables file containing critical API Keys (Groq, Gemini, Qdrant). **Do not commit this file.** |
| `main.py` | File | (Located in `app/`) The entrypoint to boot the FastAPI server. |
| `qa_runner.py` | File | High-level script for executing automated question-answer test suites. |

## ⚙️ Internal Workflow
When the server boots, it reads the `.env` file to establish connections to the external LLM providers (Groq/Gemini) and the Qdrant Cloud Vector Database.

The HTTP endpoints act as the interface:
1. **Uploads** are temporarily buffered in `storage/uploads/`, uploaded to Backblaze B2 Cloud Storage, vectorized, and pushed to Qdrant.
2. **Queries** invoke the `app/rag/rag_service.py` engine, which fetches chunks from Qdrant and streams prompts to the LLM.

## 🔧 Dependencies
* **Python 3.11+** is highly recommended.
* Ensure a virtual environment (`.venv`) is active before installing `requirements.txt`.
* The application heavily depends on `langchain-google-genai` and `langchain-groq` for LLM orchestration.

## 💡 Best Practices
* **Environment Variables:** Never hardcode API keys in the `.py` files. Always use `os.environ.get()` to pull from `.env`.
* **Testing:** Use the local `.py` scripts (like `test_hindi_local.py`) to validate LLM configurations without needing to boot the full FastAPI web server.
* **Migrations:** If the SQLite schema in `app/database/sqlite.py` changes, you must manually run the cleanup services or recreate `ratan_registry.db`.

## 🚀 Quick Start (Development)
```bash
# 1. Activate the virtual environment
source .venv/bin/activate

# 2. Run the application
uvicorn app.main:app --reload
```
