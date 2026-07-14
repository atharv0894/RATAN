# RATAN RAG Module

## Retrieval-Augmented Technology for Asset Networks

The `rag` module is the core AI retrieval and generation layer of **RATAN (Retrieval-Augmented Technology for Asset Networks)**.

RATAN is an industrial knowledge intelligence platform designed to transform fragmented asset documents, maintenance records, SOPs, manuals, and incident reports into a unified and queryable knowledge system.

The RAG module retrieves relevant industrial knowledge from the vector database and provides grounded context to the Large Language Model (LLM) for generating accurate answers.

## RAG Architecture

User Query
    ↓
Embedding Service
    ↓
Retrieval Service
    ↓
Vector Store
    ↓
Relevant Document Chunks
    ↓
RAG Service
    ↓
Groq LLM
    ↓
Grounded Answer

## Folder Structure

app/rag/
├── __init__.py
├── embedding_service.py
├── vector_store.py
├── indexer.py
├── retrieval_service.py
├── rag_service.py
└── README.md

## Components

### embedding_service.py

Responsible for generating vector embeddings from text.

Responsibilities:

- Generate document chunk embeddings
- Generate query embeddings
- Manage the embedding model
- Provide reusable embedding functionality

### vector_store.py

Manages the vector database used by RATAN.

Responsibilities:

- Initialize ChromaDB
- Create or load collections
- Manage persistent vector storage
- Provide vector database access to other RAG services

### indexer.py

Responsible for indexing processed document chunks.

Responsibilities:

- Receive document chunks
- Generate embeddings using the embedding service
- Store embeddings in the vector database
- Store chunk metadata
- Generate unique chunk IDs

### retrieval_service.py

Retrieves relevant industrial knowledge for a user query.

Responsibilities:

- Generate query embeddings
- Search the vector database
- Retrieve top-K relevant chunks
- Return document text and metadata

### rag_service.py

Orchestrates the complete Retrieval-Augmented Generation pipeline.

Responsibilities:

- Accept user queries
- Retrieve relevant document chunks
- Build LLM context
- Send grounded prompts to the Groq LLM
- Generate context-aware answers

## RAG Pipeline

1. Industrial documents are parsed.
2. Documents are divided into semantic chunks.
3. The embedding service generates embeddings.
4. The indexer stores chunks and embeddings in ChromaDB.
5. A user submits a query.
6. The retrieval service searches for relevant chunks.
7. Retrieved chunks are used to build the LLM context.
8. The RAG service sends the context and query to the Groq LLM.
9. The LLM generates a grounded answer.

## Design Principles

- Modular architecture
- Clear separation of responsibilities
- Grounded AI responses
- Reusable RAG services
- Persistent vector storage
- Asset-centric industrial knowledge retrieval

## Current MVP Stack

- Python
- FastAPI
- ChromaDB
- Sentence Transformers
- Groq LLM API

## Project

**RATAN**

Retrieval-Augmented Technology for Asset Networks