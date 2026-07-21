# Models Layer (`app/models/`)

This directory houses the foundational Pydantic data schemas used across the application to ensure strict type validation and structural integrity.

## 🏗️ Validation Architecture

```mermaid
graph TD
    Client[Client Payload] --> FastAPI[FastAPI Route]
    
    FastAPI --> Pydantic[Pydantic Model]
    
    Pydantic --> |Invalid| 422[422 Unprocessable Entity]
    Pydantic --> |Valid| Service[Service Layer]
    
    Service --> |Database Row| Serialization[Pydantic Response Model]
    Serialization --> APIResponse[APISuccessResponse]
```

*Note: With the V2 architecture update, many route-specific Pydantic models (like `ChatRequest`, `UserRegisterRequest`, and `APISuccessResponse`) have been co-located within their respective `app/api/` modules for tighter cohesion. This directory now primarily stores global application types.*

## ✨ Features
- **Type Coercion**: Automatically converts JSON strings to Python `UUID` or `datetime` objects.
- **OpenAPI Schema**: Pydantic models automatically generate the Swagger UI documentation for the frontend developers.
