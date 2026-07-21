# Platform Administration Architecture

The Platform Administration module separates internal tenant management from global, cross-tenant operational management.

## Administration Flow

```mermaid
graph TD
    SuperAdmin((SuperAdmin)) --> |Requires 'SuperAdmin' Role| AdminRouter[FastAPI Admin Router\n/api/v1/admin]
    
    AdminRouter --> AdminService[Admin Service Layer]
    
    AdminService --> |Cross-Tenant Queries| Orgs[Organizations Management]
    AdminService --> |Global Access| Users[Global User Management]
    AdminService --> |RBAC Config| Roles[Role Definition Management]
    AdminService --> |Upsert| Settings[System Settings & Limits]
    
    AdminService --> |Trigger Jobs| Maintenance[Maintenance Operations]
    Maintenance --> Reindex[Global Reindex]
    Maintenance --> Cleanup[Orphan Cleanup]
    Maintenance --> Repair[Vector Integrity Repair]
    
    AdminService --> |Read Only| AuditLogs[Global Audit Logs]
```

## Core Responsibilities
- **Global Control**: Standard routes (`/api/v1/users`) are strictly bound to the caller's tenant. The `/api/v1/admin` routes bypass tenant restrictions, explicitly requiring the highest level of authorization.
- **Dynamic Configuration**: System settings (limits, configurations, API fallbacks) are managed here and persisted to the DB, preventing the need for environment variable restarts.
- **Maintenance**: Triggers asynchronous repair and cleanup jobs to ensure storage (B2) and vectors (Qdrant) remain perfectly synchronized with relational metadata (SQLite).
