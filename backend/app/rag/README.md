# 🧠 RAG (Retrieval-Augmented Generation) Core Engine

> [!IMPORTANT]
> This directory represents the heart of the RATAN Intelligence Platform. It orchestrates the semantic chunking, vector embedding, similarity retrieval, and LLM reasoning pipelines.

## 🎯 Purpose and Responsibilities

The `rag` module abstracts the complexities of the Hugging Face embedding models, Qdrant vector similarity algorithms, and the Groq/Gemini LLM generation routing. It ensures that incoming PDFs are correctly decomposed into semantically meaningful chunks and that user queries fetch the absolute most relevant context before reasoning.

## 📄 Core Architecture

| Component | Responsibility |
|-----------|----------------|
| `chunker.py` | Implements recursive character splitting with overlap (1500 chars / 200 overlap). Ensures markdown tables and sentences are never split in the middle. |
| `document_loaders.py` | Uses `pdfplumber` to extract precise text, page numbers, and spatial layout data from raw PDFs. |
| `embedding_service.py` | Wrapper for `BAAI/bge-m3`. Projects text chunks into a 1024-dimensional dense vector space optimized for multilingual semantic similarity. |
| `qdrant_store.py` | The interface to the Qdrant Cloud Cluster. Handles indexing payloads and conducting Cosine Similarity searches. |
| `retrieval_service.py` | Implements Maximal Marginal Relevance (MMR) reranking to maximize diversity and reduce duplicate context injected into the LLM. |
| `rag_service.py` | The master orchestration class. Manages the primary (`openai/gpt-oss-120b`) and fallback (`gemini-2.5-flash`) LLM generation, injecting the retrieved context into a strict citation-enforced prompt. |
| `prompt_builder.py` | (If utilized) Constructs the strict JSON-enforced instruction prompts. |

## ⚙️ Data Flow

1. **Ingestion Flow:** `document_loaders.py` -> `chunker.py` -> `embedding_service.py` -> `qdrant_store.py`
2. **Chat Flow:** Query -> `embedding_service.py` -> `qdrant_store.py` -> `retrieval_service.py` -> `rag_service.py`

## 🛡️ Resiliency & Fallback
The `rag_service.py` features a self-healing LLM backoff mechanism. If the primary Groq model encounters a `429 Too Many Requests` (Rate Limit), the service naturally suspends and retries. If a hard `500/503` outage occurs, it instantly falls back to the Google Gemini Flash model, ensuring the end-user always receives an answer.
