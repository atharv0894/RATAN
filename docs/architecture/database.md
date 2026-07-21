# Database Architecture

RATAN utilizes SQLite (V2 Schema) as its primary metadata store, optimized with comprehensive indexing and referential integrity (Foreign Keys) to support multi-tenant enterprise features.

## Entity Relationship Diagram

```mermaid
erDiagram
    organizations ||--o{ plants : contains
    plants ||--o{ departments : contains
    organizations ||--o{ users : employs
    roles ||--o{ users : assigns
    
    users ||--o{ document_versions : uploads
    users ||--o{ chat_sessions : owns
    
    organizations ||--o{ documents : owns
    documents ||--o{ document_versions : has_history
    
    chat_sessions ||--o{ chat_messages : contains
    chat_messages ||--o{ feedback : receives
    
    users ||--o{ audit_logs : triggers
    
    documents {
        string id PK
        string filename
        string status
        string organization FK
        float deleted_at
    }
    
    document_versions {
        string id PK
        string document_id FK
        int version_number
        string checksum
        string storage_path
        int is_latest
    }
    
    users {
        string id PK
        string org_id FK
        string role_id FK
        string email
        string password_hash
        int is_deleted
    }
    
    roles {
        string id PK
        string name
        string permissions
    }
    
    chat_sessions {
        string id PK
        string user_id FK
        string title
        string status
    }
    
    chat_messages {
        string id PK
        string session_id FK
        string role
        string content
        float confidence_score
        string search_filters
    }
    
    processing_jobs {
        string id PK
        string target_id
        string status
        string error_message
    }
    
    system_settings {
        string id PK
        string setting_key
        string setting_value
    }
```

## Design Principles
- **Soft Deletion**: Entities like `users`, `organizations`, and `documents` are never immediately dropped. They utilize `is_deleted = 1` or `deleted_at = timestamp` to maintain audit compliance and historical referential integrity.
- **Tenant Isolation**: Almost every major table has a direct or indirect path to `organization_id`, ensuring simple, bulletproof row-level security checks in the Service Layer.
