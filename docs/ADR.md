# Architecture Decision Records (ADR)

This document captures the key architectural decisions made during the development of RATAN, detailing the technical context, the considered alternatives, and the rationale behind each choice. This provides a blueprint for understanding the system's design constraints, especially regarding memory limits (512MB RAM) and performance requirements.

## ADR 001: FastAPI for Backend Framework
* **Status**: Accepted
* **Context**: We needed a high-performance backend capable of handling both standard REST endpoints and asynchronous, long-lived connections for Server-Sent Events (SSE) streaming during AI chat generation.
* **Decision**: We chose **FastAPI**.
* **Rationale**: FastAPI natively supports asynchronous operations (`async`/`await`), which is critical for non-blocking network I/O when streaming LLM tokens. It also provides automatic OpenAPI schema generation (Swagger UI) and Pydantic validation, reducing boilerplate code and ensuring strict type safety on data boundaries.

## ADR 002: Next.js (App Router) for Frontend
* **Status**: Accepted
* **Context**: The frontend needed to be highly responsive, support complex state management (like streaming chats and interactive PDF citations), and be easily deployable on modern edge networks (like Vercel).
* **Decision**: We chose **Next.js 14** using the App Router.
* **Rationale**: Next.js provides a robust foundation for building React applications. The App Router allows for intuitive layout nesting. We strictly utilized Client Components (`"use client"`) for the interactive dashboard while leveraging the framework's routing structure to separate the `personal` and `enterprise` namespaces cleanly.

## ADR 003: Qdrant for Vector Database
* **Status**: Accepted
* **Context**: The Retrieval-Augmented Generation (RAG) pipeline requires a highly efficient vector database to perform similarity searches on embedded document chunks.
* **Decision**: We chose **Qdrant**.
* **Rationale**: Qdrant offers excellent Rust-based performance, comprehensive support for payload metadata filtering (crucial for our tenant isolation and RBAC), and a seamless Python client. It is also lightweight enough to run efficiently in constrained environments and can be easily scaled horizontally in production.

## ADR 004: TiDB (MySQL-compatible) vs. SQLite
* **Status**: Accepted
* **Context**: The system needed a relational database to store users, organizations, document metadata, and chat histories. 
* **Decision**: The system utilizes **SQLite** for rapid local prototyping and test fixtures, but is architected to seamlessly transition to **TiDB** (Serverless MySQL) for production deployments.
* **Rationale**: The Repository Pattern allows us to swap out database connectors without altering business logic. TiDB offers serverless scaling and MySQL compatibility, while SQLite ensures tests run isolated, ephemerally, and without network overhead.

## ADR 005: Backblaze B2 for Object Storage
* **Status**: Accepted
* **Context**: Users upload raw PDF and text documents that must be securely stored and retrieved by the ingestion pipeline.
* **Decision**: We chose **Backblaze B2**.
* **Rationale**: B2 offers an S3-compatible API at a fraction of the cost of AWS S3. It integrates perfectly with our Python `boto3` client, providing a reliable, externalized object store that prevents our ephemeral backend filesystem from overflowing.

## ADR 006: Server-Sent Events (SSE) for Chat Streaming
* **Status**: Accepted
* **Context**: LLM inference (especially for large models generating long answers) takes several seconds. Waiting for the complete response degrades UX (Time-To-First-Byte > 3s).
* **Decision**: We implemented **Server-Sent Events (SSE)** using FastAPI's `StreamingResponse` and the native DOM `fetch` API.
* **Rationale**: WebSockets were deemed overkill for a unidirectional stream (Server -> Client). SSE operates over standard HTTP, bypasses complex handshake overhead, and easily passes through standard load balancers and reverse proxies (like Nginx or Render's ingress).

## ADR 007: Stateless JWT Authentication
* **Status**: Accepted
* **Context**: Managing user sessions securely across the frontend and backend without introducing a stateful caching layer (like Redis) which would violate the 512MB RAM limit.
* **Decision**: We chose **Stateless JWT (JSON Web Tokens)**.
* **Rationale**: The backend validates the JWT cryptographically without needing a database lookup for every request. The `tenant` and `role` claims are embedded in the token, allowing immediate authorization decisions.

## ADR 008: Lazy Loading ML Models
* **Status**: Accepted
* **Context**: The deployment target (Render Free/Starter tier) imposes a strict 512MB RAM limit. Eagerly loading the embedding model (`BAAI/bge-small-en-v1.5`) alongside the FastAPI server caused Out-Of-Memory (OOM) crashes during startup.
* **Decision**: We implemented **Lazy Loading / Singleton Patterns** for the Embedding engine.
* **Rationale**: The `TextEmbedding` model is only instantiated the first time a user queries the RAG pipeline or uploads a document. This spreads the memory spike and ensures the core HTTP server boots instantaneously and remains healthy.

## ADR 009: Clean Architecture (Repository Pattern)
* **Status**: Accepted
* **Context**: The backend required long-term maintainability, testability, and separation of concerns to avoid "Fat Routers".
* **Decision**: We enforced **Clean Architecture boundaries**.
* **Rationale**: The API Routers handle HTTP parsing. The Service Layer handles business logic (RAG orchestration). The Repository Layer handles database/vector storage. This enabled us to write unit tests that mock the database layer, executing the full AI pipeline in under a second.
