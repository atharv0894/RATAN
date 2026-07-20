# Entity Extraction (`app/entity/`)

This module leverages Natural Language Processing (NLP) to dynamically extract explicit entities from uploaded documents.

## Core Features
- Extracts domain-specific entities (e.g., Plant Names, Equipment IDs, Personnel, Dates).
- `entity_extractor.py`: Parses text and maintains extraction mapping in the SQLite metadata DB.
- These entities are later utilized by the RAG `SearchEngine`'s `QueryAnalyzer` to automatically map conversational inputs to hard SQL/Qdrant filters.
