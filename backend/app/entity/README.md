# 📁 Entity Directory

This directory contains components related to `entity` functionality in the RATAN RAG backend.

## 🎯 Purpose and Responsibilities

Provides encapsulated modules and services for this specific domain. Ensure any modifications adhere to the existing architecture.

## 📄 Files Overview

| File | Description |
|------|-------------|
| `entity_extractor.py` | Class EntityExtractor |
| `entity_models.py` | Class EntityBase, Class EntityResponse, Class ExtractedEntitiesResponse... |
| `entity_patterns.py` | Core implementation file. |

## ⚙️ Internal Workflow
Files in this directory interact closely. Service files generally orchestrate operations, while utility or model files define the schemas and algorithms.

## 🔧 Dependencies
- **Incoming**: Modules that require these features will import them.
- **Outgoing**: Relies on standard libraries, LangChain, Qdrant, and SQLite.

## 💡 Best Practices
- Keep business logic isolated in service classes.
- Maintain type hints and comprehensive docstrings.
- Avoid circular imports.
