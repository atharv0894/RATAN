# Resume & Interview Preparation Guide

This document is designed to help you present the RATAN project effectively on your resume and during technical interviews. It translates the engineering work into impactful bullet points and conversational scripts.

## 1. Resume Bullet Points (Action-Oriented)

*   **Architected and deployed a multi-tenant Enterprise Knowledge Platform (RATAN)** using Next.js and FastAPI, securely isolating user workspaces and corporate namespaces via stateless JWT authentication.
*   **Engineered an industrial-grade Retrieval-Augmented Generation (RAG) pipeline** utilizing Qdrant (Vector DB), FastEmbed, and Groq/Gemini LLMs, reducing information retrieval time across technical manuals to under 300ms.
*   **Optimized backend memory utilization by 40%** to operate strictly within a 512MB RAM constraint by implementing Singleton patterns and lazy-loading for Machine Learning embedding models.
*   **Implemented Server-Sent Events (SSE) streaming** for real-time LLM token generation, reducing perceived Time-To-First-Token (TTFB) to < 500ms and significantly improving the UI/UX responsiveness.
*   **Designed a decoupled Clean Architecture** utilizing the Repository and Dependency Injection patterns, enabling 100% unit test coverage for the AI pipeline using ephemeral in-memory SQLite fixtures.
*   **Built a dynamic, responsive frontend UI** with Next.js App Router, Tailwind CSS, and Framer Motion, featuring progressive chat interfaces, Markdown citation rendering, and secure OAuth integrations.

## 2. Recruiter Summary (The "Elevator Pitch")
**"What is RATAN?"**
> "RATAN is a production-ready, full-stack AI platform I built that acts as an intelligent knowledge assistant for both personal users and large enterprises. It allows companies to securely upload thousands of technical manuals and instantly query them using AI, with strict role-based access controls to ensure data privacy. I built the backend in Python using FastAPI and Qdrant for blazing-fast vector search, and the frontend in React using Next.js. The biggest technical challenge I solved was optimizing the AI pipeline to run asynchronously and stream tokens back to the user instantly, all while operating under a strict 512MB memory limit on the cloud."

## 3. The 2-Minute Technical Explanation (For Hiring Managers)
> "RATAN is separated into a decoupled Next.js frontend and a FastAPI backend. 
> 
> When a user logs in via JWT, they are routed to either a Personal or Enterprise workspace. When they upload a document (like a PDF), the backend securely stores the raw file in Backblaze B2, extracts the text, chunks it, and generates dense vector embeddings using a local BGE-Small model. These embeddings are indexed into Qdrant with metadata tracking their tenant ID for secure isolation.
> 
> When a user asks a question, the backend embeds the query, performs a cosine similarity search in Qdrant—filtering strictly by their organization ID—and injects the top-K relevant chunks into a system prompt. This prompt is sent to a high-speed LLM via Groq. Instead of blocking the server while the AI generates the answer, I implemented Server-Sent Events (SSE) using Python asynchronous generators. This streams the text back to the React frontend chunk-by-chunk, providing that native, real-time ChatGPT-like experience."

## 4. The 15-Minute Architecture Walkthrough (For Systems Design Interviews)

If asked to draw or explain the architecture deeply, hit these key components:

1.  **The API Layer (FastAPI):** Explain why you chose FastAPI (async support, Pydantic validation). Mention that endpoints are lightweight and immediately hand off to the Service Layer.
2.  **Authentication & Security (JWT):** Explain how stateless JWTs prevent database bottlenecks. The JWT contains the `user_id`, `role`, and `organization_id`. The API extracts these claims to enforce multi-tenancy at the query level (preventing IDOR).
3.  **The Storage Layer (B2 + SQLite/TiDB + Qdrant):** 
    *   *Raw Files:* Backblaze B2 (cheap, reliable object storage).
    *   *Relational Data:* SQLite/TiDB (users, session history).
    *   *Vector Data:* Qdrant (fast, Rust-based similarity search).
4.  **The RAG Pipeline (Clean Architecture):** 
    *   Explain the separation of concerns: `DocumentProcessor` (chunking) -> `EmbeddingService` (vectorization) -> `QdrantStore` (storage). 
    *   *Crucial Talking Point:* Explain how you avoided OOM (Out Of Memory) errors by lazy-loading the embedding model.
5.  **The Streaming Engine (SSE):** Detail how HTTP polling or WebSockets were evaluated, but SSE was chosen as the optimal protocol for unidirectional LLM token streaming.

## 5. Anticipated Interview Q&A

**Q: Why didn't you use LangChain for the entire backend?**
*A:* "While I used LangChain for basic text splitting, I intentionally wrote the core RAG orchestration, retrieval logic, and prompt construction natively. Frameworks like LangChain can become overly abstracted 'black boxes' that make it difficult to optimize for latency, memory, and custom tenant filtering. Writing the orchestrator myself allowed me to precisely manage the async event loop for SSE streaming."

**Q: How did you handle the 512MB RAM constraint on Render?**
*A:* "Memory management was a primary engineering constraint. I solved this in three ways: First, I swapped large models for the highly efficient `BAAI/bge-small-en-v1.5` which operates under 150MB. Second, I implemented a Singleton pattern with lazy-loading, ensuring the ML models only load into RAM exactly when needed, keeping the startup footprint tiny. Third, I streamed large file uploads directly to disk/B2 rather than holding them in memory."

**Q: How do you ensure Enterprise Data Privacy?**
*A:* "Every document chunk in the Qdrant vector database is tagged with an `organization_id` payload. When a query is executed, the backend securely extracts the user's tenant ID from their validated JWT and hard-codes a `must` filter clause into the Qdrant query. The LLM physically cannot see data from another tenant, even if it tries."
