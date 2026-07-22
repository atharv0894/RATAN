# Security Architecture

Security in RATAN is enforced across multiple layers, ensuring deep tenant isolation, explicit role validation, and comprehensive auditability.

## Security Layers

```mermaid
graph TD
    Request([Incoming Request]) --> Gateway[API Gateway / TLS Termination]
    Gateway --> JWTMiddleware[JWT Authentication Middleware]
    
    JWTMiddleware --> |Invalid| 401[401 Unauthorized]
    JWTMiddleware --> |Valid Payload| RBACMiddleware[Strict RBAC Check]
    
    RBACMiddleware --> |Missing Role| 403[403 Forbidden]
    RBACMiddleware --> |Authorized| TenantContext[Tenant Context Injection]
    
    TenantContext --> ServiceLayer[Service Logic Execution]
    
    ServiceLayer --> SQLIsolation{SQL DB Isolation}
    SQLIsolation --> |org_id match| DB[Execute Relational Query]
    SQLIsolation --> |Mismatch| 404[404 Not Found]
    
    ServiceLayer --> VectorIsolation{Vector DB Isolation}
    VectorIsolation --> |metadata.organization_id| Qdrant[Execute Vector Query]
    VectorIsolation --> |Mismatch / Injection| 403_Vector[Block Retrieval]
    
    DB --> AuditLog[Write to Audit Log]
```

## Core Tenets

1. **JWT (JSON Web Tokens)**: Cryptographically signed tokens establish identity without persistent session lookups, maintaining stateless, high-performance horizontal scaling. Refresh tokens are tracked in `user_sessions` and can be forcibly revoked by administrators.
2. **Strict Role-Based Access Control (RBAC)**: Fine-grained permissions are assigned to roles, which are assigned to users. FastAPI Dependency Injection (`Depends(RequireRole(["Admin"]))`) ensures endpoints are secure by default. **Important:** The dependency strictly blocks Tenant Admins from accessing global SuperAdmin endpoints, fully preventing privilege escalation.
3. **Relational Tenant Isolation**: The `get_tenant_context` dependency implicitly injects the user's `organization_id`. Every single `WHERE` clause in the Repository layer enforces this boundary. Cleanup services, dashboards, and job endpoints execute explicit `JOIN` operations against the `organizations` context to prevent Insecure Direct Object Reference (IDOR).
4. **Vector Payload Bounding**: To prevent "Tenant Hopping" via LLM prompt injection (e.g. asking the AI to search another organization's data), Qdrant queries force a strict `FieldCondition` match on `metadata.organization_id` derived exclusively from the authenticated JWT. The system intentionally applies the tenant context *after* user-supplied filters to override any malicious parameters.
5. **Prompt Injection Protection**: The LLM System Prompt instructs the model to treat all user input and retrieved chunks as malicious, unexecutable data. 
6. **Audit Logging**: Every mutating action (Upload, Delete, Config Change) triggers an asynchronous write to the `audit_logs` table, attaching the exact IP, endpoint, user, and execution latency. Bounded by tenant context.
