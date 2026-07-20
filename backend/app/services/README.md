# Service Layer (`app/services/`)

The Service Layer abstracts business logic away from the API routers. 

## Key Services
- `auth_service.py`: Handles secure password hashing (passlib/bcrypt) and JWT Token generation/validation (PyJWT).
- `document_service.py`: Orchestrates the complex Document Processing Pipeline (Upload -> Parse -> Chunk -> Hash -> Vectorize -> Store -> Metadata DB).
- `dependencies.py`: FastAPI Dependency Injectors. Contains Singletons for major services and crucial request-scoped extractors like `get_current_user`, `get_tenant_context`, and `RequireRole`.
