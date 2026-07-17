# 📁 Api Directory

This directory contains components related to `api` functionality in the RATAN RAG backend.

## 🎯 Purpose and Responsibilities

Provides encapsulated modules and services for this specific domain. Ensure any modifications adhere to the existing architecture.

## 📄 Files Overview

| File | Description |
|------|-------------|
| `chat.py` | Function chat |
| `cleanup.py` | Function run_cleanup |
| `documents.py` | Function list_documents, Function get_document, Function delete_document... |
| `entities.py` | Function get_all_entities, Function search_entities_by_name, Function get_document_entities |
| `health.py` | Function get_health |
| `stats.py` | Function get_stats |

## ⚙️ Internal Workflow
Files in this directory interact closely. Service files generally orchestrate operations, while utility or model files define the schemas and algorithms.

## 🔧 Dependencies
- **Incoming**: Modules that require these features will import them.
- **Outgoing**: Relies on standard libraries, LangChain, Qdrant, and SQLite.

## 💡 Best Practices
- Keep business logic isolated in service classes.
- Maintain type hints and comprehensive docstrings.
- Avoid circular imports.
