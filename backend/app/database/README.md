# 🗄️ Database Management

> [!CAUTION]
> This module manages the relational state of the application. Do not confuse this with the Vector Database (Qdrant) which handles semantic search. This SQLite database acts as a traditional metadata registry.

## 🎯 Purpose and Responsibilities

The `database` directory isolates the relational state of the application. It ensures that when a user uploads a PDF, the UI can continuously poll the backend to see if the document is `Processing`, `Ready`, or `Failed`. 

## 📄 Schema

The primary table is `documents`, defined in `sqlite.py`. It tracks:
* `document_id` (Primary Key UUID)
* `filename`
* `status` (Processing, Indexed, Failed)
* `upload_time`
* `checksum_sha256` (Used for deduplication)
* `file_size`, `mime_type`, `page_count`, `chunk_count`

## ⚙️ Usage
To interact with the database, services import the `get_db_connection` context manager. 
```python
from app.database.sqlite import get_db_connection

conn = get_db_connection()
conn.execute("SELECT * FROM documents")
```

> [!NOTE]
> If you make changes to the schema inside `sqlite.py`, you will need to delete the `ratan_registry.db` file in the backend root so it regenerates on the next boot.
