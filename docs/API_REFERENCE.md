# API Reference

All API routes are prefixed with `/api/v1` and generally follow RESTful conventions. All responses are wrapped in a standard JSON envelope:
```json
{
  "success": true,
  "data": { ... }
}
```

## Authentication (`/auth`, `/personal/auth`, `/enterprise/auth`)

### `POST /api/v1/personal/auth/login`
- **Body**: OAuth2 Form Data (`username`, `password`)
- **Response**: JWT Access and Refresh Tokens.

### `POST /api/v1/personal/auth/google`
- **Body**: `{ "token": "google_id_token" }`
- **Response**: JWT Tokens.

### `POST /api/v1/auth/refresh`
- **Body**: `{ "refresh_token": "..." }`
- **Response**: New JWT Access Token.

## Personal AI (`/personal/chat`)

### `GET /api/v1/personal/chat`
- **Headers**: `Authorization: Bearer <token>`
- **Response**: List of personal chat sessions.

### `POST /api/v1/personal/chat`
- **Body**: `{ "title": "New Session" }`
- **Response**: Chat Session ID.

### `POST /api/v1/personal/chat/message`
- **Body**: 
```json
{
  "question": "What is the procedure?",
  "chat_history": [{"role": "user", "content": "..."}],
  "session_id": "uuid"
}
```
- **Response**: `text/event-stream` (Server-Sent Events). Returns JSON chunks of `{ "type": "chunk", "text": "..." }` followed by `{ "type": "done", "full_answer": "...", "citations": [...] }`.

## Enterprise AI (`/chat`)

### `POST /api/v1/chat`
- **Body**: `{ "title": "New Chat Session" }`
- **Response**: Chat Session ID.

### `POST /api/v1/chat/message`
- **Body**: Same as Personal chat `message`, but uses Enterprise Context.
- **Response**: `text/event-stream` (Server-Sent Events). Returns progressive token chunks for real-time UI typing indicators.

### `POST /api/v1/chat/search`
- **Body**: Same as above.
- **Response**: Synchronous JSON `RAGResponse`. Used by the Global Semantic Search UI when streaming is not desired.

## Documents (`/documents`)

### `POST /api/v1/documents`
- **Body**: `multipart/form-data` containing the file upload.
- **Headers**: `Authorization: Bearer <token>`
- **Response**: Document ID, triggering the background indexing pipeline.

### `GET /api/v1/documents`
- **Response**: List of uploaded organizational documents.

## Dashboard Stats (`/dashboard`)

### `GET /api/v1/dashboard/stats`
- **Response**: System usage, active users, total documents indexed.

### `GET /api/v1/dashboard/analytics/chat`
- **Response**: Time-series data of chat engagement.
