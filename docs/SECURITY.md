# Security & Data Isolation Architecture

Security is a foundational pillar of RATAN, particularly because it hosts sensitive enterprise documentation alongside private personal workspaces.

## 1. Tenant Data Isolation

Data isolation is enforced at the database level and the vector database level.

### Relational Database
- **Organizations**: Users are bound to an `org_id`. All queries for documents, chat histories, and users include `WHERE org_id = ?` dynamically through FastAPI dependencies (`get_tenant_context`).
- **Personal**: Queries validate the `account_type == "PERSONAL"` and restrict access by `WHERE user_id = ?`.

### Vector Database (Qdrant)
The RAG pipeline never performs global searches. 
Before hitting the `QdrantStore`, the `RAGService` explicitly injects a payload filter:
- **Enterprise**: `base_where = {"organization_id": user["org_id"]}`
- **Personal**: `base_where = {"namespace": f"personal/{user_id}"}`

Because this filter is enforced securely inside the backend route logic, it is structurally impossible for data to bleed across tenants or between personal and enterprise workspaces.

## 2. Authentication

RATAN uses stateless JWT authentication.
- **Tokens**: `access_token` (short-lived, 30m) and `refresh_token` (long-lived, 7d).
- **Storage**: Tokens are sent via HTTP headers (`Authorization: Bearer`). 
- **Validation**: The `auth_service.py` decodes the token and verifies the signature using `JWT_SECRET_KEY`.

## 3. Role-Based Access Control (RBAC)

FastAPI dependencies are used to enforce route-level authorization.

```python
# Ensures user is authenticated and part of a valid organization
@router.get("")
def get_dashboard(current_user: dict = Depends(RequireOrganizationUser)):
    ...

# Enforces strict role access
@router.post("")
def create_plant(current_user: dict = Depends(RequireRole(["Admin", "Manager"]))):
    ...
```

## 4. API Security

- **CORS**: `CORSMiddleware` is configured to explicitly allow trusted frontend domains (e.g., `ratan-six.vercel.app`), preventing unauthorized Cross-Origin requests.
- **SQL Injection**: The backend uses parameterized queries `(?, ?)` in SQLite to completely eliminate SQL injection vectors.
- **Validation**: All incoming API payloads are strictly validated using Pydantic schemas (e.g., `ChatRequest`, `LoginRequest`).

## 5. File Upload Validation

When users upload files for RAG processing:
1. The MIME type is checked against an allowed list (`application/pdf`, `text/plain`, etc.).
2. The file is streamed into memory chunks to prevent out-of-memory DDoS attacks.
3. The backend assigns a secure UUID to the file.

## 6. Secrets Management

- Secrets are never hardcoded.
- Environments are managed via `.env` files locally and secure environment variables in Render/Vercel.
- Database passwords and API keys (Groq, Gemini, Qdrant) are tightly scoped.
