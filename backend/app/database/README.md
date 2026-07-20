# Database Layer (`app/database/`)

This module manages the local SQLite database which serves as the **Single Source of Truth** for the RATAN platform's relational metadata. 

**Note: Document text chunks and vectors are NEVER stored here. They belong in Qdrant.**

## Core Components
- `schema.py`: Defines the V2 Enterprise normalized database schema, encompassing `users`, `roles`, `organizations`, `documents`, `document_versions`, and `audit_logs`.
- `sqlite.py`: Handles connection pooling, thread-local connections (`check_same_thread=False`), and SQLite-specific pragmas like WAL mode for performance.

## Migrations
Migrations are handled declaratively via `migrations.py` to seamlessly upgrade V1 schemas to the current V2 Enterprise architecture without data loss.
