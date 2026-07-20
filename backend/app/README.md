# Application Core (`app/`)

The `app` directory houses the entire FastAPI application logic, structured using clean architecture principles.

## Architecture Guidelines
- **API Routers (`api/`)**: Handle HTTP requests, responses, and validation via Pydantic. Should contain ZERO heavy business logic.
- **Services (`services/`)**: The "Brain" of the application. Orchestrates logic between the database, RAG pipeline, and external APIs.
- **RAG Engine (`rag/`)**: Encapsulates LLM interaction, chunking, indexing, and the modular Search Engine (Strategy Pattern).
- **Storage & Database**: Abstracted behind interfaces (Repository Pattern) to allow seamless swapping (e.g., SQLite -> PostgreSQL).

## Key Files
- `main.py`: Bootstraps the application, registers routes, attaches CORS/Audit middlewares, and maps global exception handlers.
- `exceptions.py`: Centralizes domain-specific exceptions (e.g., `NotFoundError`, `AuthenticationError`) mapped to standardized JSON payloads.
