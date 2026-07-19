# 📦 Data Models & Schemas

> [!TIP]
> The `models` directory is built using Pydantic. It strictly defines the shape of all incoming requests and outgoing responses across the FastAPI application.

## 🎯 Purpose and Responsibilities

To guarantee that invalid data never reaches the core algorithms. By defining strict types, FastAPI will automatically reject malformed HTTP requests and generate the live interactive Swagger UI documentation.

## 📄 Core Models

| File | Description |
|------|-------------|
| `requests.py` | Contains schemas for incoming API requests. Example: `ChatRequest` which enforces that every query must contain a `question` string. |
| `responses.py` | Contains schemas for outgoing API data. Example: `ChatResponse` which enforces that the RAG engine must return a string `answer` and a list of `citations`. |

## ⚙️ Why Pydantic?
Pydantic ensures runtime type-checking. If a client sends `{"question": 12345}` instead of a string, Pydantic throws a validation error before the JSON ever touches the RAG pipeline. This prevents catastrophic internal server errors (HTTP 500) and returns clean HTTP 422 errors instead.
