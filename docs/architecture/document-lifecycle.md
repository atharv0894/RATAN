# Document Lifecycle

The Document Lifecycle governs how raw files transition from a user upload into a verifiable, embedded, and version-tracked Knowledge Base asset.

## Lifecycle Diagram

```mermaid
graph TD
    Upload([User Uploads File]) --> Validation[MIME & Size Validation]
    Validation --> Metadata[Attach Tenant & Knowledge Metadata]
    Metadata --> Versioning{Version Check}
    
    Versioning -->|New File| CreateDoc[Create Document Record]
    Versioning -->|Existing| CreateVersion[Increment Version Number]
    
    CreateDoc --> Storage[Upload to Backblaze B2]
    CreateVersion --> Storage
    
    Storage --> DBCommit[Commit Version to SQLite]
    DBCommit --> ProcessingJob[Queue Processing Job]
    
    ProcessingJob --> Parsing[Parse Text from Binary]
    Parsing --> Chunking[Split into Semantic Chunks]
    Chunking --> Embeddings[Generate Vector Embeddings]
    Embeddings --> Qdrant[Upsert to Qdrant Cloud]
    
    Qdrant --> READY([Status: READY])
```

## Document States

```mermaid
stateDiagram-v2
    [*] --> UPLOADING: User submits file
    UPLOADING --> QUEUED: B2 success, DB committed
    QUEUED --> PROCESSING: Job worker picks up
    PROCESSING --> EMBEDDING: Text parsed & chunked
    EMBEDDING --> INDEXING: Vectors generated
    INDEXING --> READY: Inserted to Qdrant
    
    PROCESSING --> FAILED: Parser Error
    EMBEDDING --> FAILED: API Timeout
    
    READY --> ARCHIVED: Superseded by new version
    READY --> DELETED: Soft deleted by user
    DELETED --> [*]: Hard cleanup job
```

## Immutable Versioning
Documents are never modified in place. When a user updates a document, a new `document_versions` record is created. The old version is marked `is_latest = 0` (Archived state), and the new version becomes `is_latest = 1`. This preserves historical context for old chat sessions that may have cited the older version.
