# 📁 Services Directory

This directory contains components related to `services` functionality in the RATAN RAG backend.

## 🎯 Purpose and Responsibilities

Provides encapsulated modules and services for this specific domain. Ensure any modifications adhere to the existing architecture.

## 📄 Files Overview

| File | Description |
|------|-------------|
| `cleanup_service.py` | Class CleanupService |
| `dependencies.py` | Function get_embedding_service, Function get_vector_store, Function get_retrieval_service... |
| `document_service.py` | Class DocumentService |

## ⚙️ Internal Workflow
Files in this directory interact closely. Service files generally orchestrate operations, while utility or model files define the schemas and algorithms.

## 🔧 Dependencies
- **Incoming**: Modules that require these features will import them.
- **Outgoing**: Relies on standard libraries, LangChain, Qdrant, and SQLite.

## 💡 Best Practices
- Keep business logic isolated in service classes.
- Maintain type hints and comprehensive docstrings.
- Avoid circular imports.
