# 🧬 NLP Entity Extraction

> [!NOTE]
> The `entity` module provides heuristic and regex-based Natural Language Processing to detect patterns in textual data before it is embedded into the vector space.

## 🎯 Purpose and Responsibilities

While the RAG Engine handles semantic similarity, the Entity Extractor performs deterministic extraction. It identifies dates, technical part numbers, financial figures, and document types, allowing the system to perform exact-match metadata filtering in Qdrant (e.g., "Filter by Year=2009").

## 📄 Core Files

| File | Responsibility |
|------|----------------|
| `entity_extractor.py` | The main interface. Analyzes text chunks and extracts structured JSON entities (Dates, Organizations, Metrics). |
| `entity_patterns.py` | Contains the complex Regular Expressions (Regex) used to reliably parse complex industrial data. |
| `entity_models.py` | Pydantic classes defining the strict structure of an extracted entity (ensuring no schema drift). |

## 💡 Future Scope
Currently, the module relies heavily on regex and heuristics. In future iterations, this can be upgraded to use zero-shot Named Entity Recognition (NER) via a lightweight local LLM or spaCy model to extract highly context-dependent industrial nomenclature.
