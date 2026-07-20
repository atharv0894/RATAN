# Storage Layer (`app/storage/`)

This module manages the physical storage of user-uploaded files, totally decoupled from the vector search and metadata database.

## Components
- `storage_service.py`: A unified Factory interface that routes upload/download commands based on the configured environment.
- `local_storage.py`: For local testing/hackathon mode. Saves raw documents to a local `/storage` directory.
- `b2_storage.py`: Enterprise cloud driver leveraging Backblaze B2 (S3-compatible API). Ideal for infinite scaling and persistent high-availability document storage.
