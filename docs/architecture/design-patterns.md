# Design Patterns

RATAN utilizes several enterprise software design patterns to maintain code quality, testability, and separation of concerns.

## 1. Repository Pattern
- **Where**: `backend/app/database/repositories.py`
- **Why**: Isolates the domain logic from the underlying data access technology. If the database switches from SQLite to PostgreSQL, the Service layer remains completely untouched.

## 2. Service Layer
- **Where**: `backend/app/services/*_service.py`
- **Why**: Keeps routers (controllers) incredibly thin. Services contain all business rules, orchestration, and validation logic, making them highly reusable and easily testable without needing active HTTP contexts.

## 3. Dependency Injection
- **Where**: `backend/app/services/dependencies.py`
- **Why**: FastAPI heavily utilizes DI. We use it to inject authenticated user contexts (`get_current_user`), enforce roles (`RequireRole`), and inject database connections. This removes global state and makes unit testing trivial.

## 4. Compensating Transaction Pattern (Fallback)
- **Where**: `backend/app/rag/rag_service.py`
- **Why**: Cloud LLMs (Groq) can experience rate limits or outages. The RAG service wraps the primary LLM call in a `try/except`. On failure, it falls back to a completely different provider (Gemini).

## 5. Factory / Builder Pattern
- **Where**: `backend/app/rag/prompt_builder.py` and `context_builder.py`
- **Why**: Encapsulates the complex logic of assembling the final LLM prompt string from chat history, system instructions, and retrieved context chunks.
