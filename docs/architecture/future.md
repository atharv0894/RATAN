# Future Architecture & Scaling

While the current architecture is robust for mid-sized enterprise deployments, scaling to millions of documents requires infrastructural evolutions.

## 1. PostgreSQL Migration
**Current**: SQLite (File-based, highly concurrent reads, locked writes).
**Future**: Migrate the repository layer to PostgreSQL using SQLAlchemy or raw asyncpg. This unlocks horizontal scaling of the API servers without SQLite file-locking contention.

## 2. Background Workers (Celery/Redis)
**Current**: File processing, chunking, and embedding happen synchronously during the request cycle (or via simple background tasks).
**Future**: Implement Celery with a Redis broker. Long-running OCR jobs and mass-reindexing tasks can be distributed across a cluster of worker nodes, providing status updates via WebSockets.

## 3. Redis Caching
**Current**: SQL queries hit the disk/memory DB directly.
**Future**: Introduce a Redis cache layer in front of the Dashboard and Organization services. Analytical queries and RBAC token validations can be cached to heavily reduce database load.

## 4. Multi-Region Deployment
**Current**: Single region API gateway.
**Future**: Deploy stateless FastAPI containers across multiple global regions. Connect them to a globally replicated vector database (Qdrant) and a geo-replicated object store (B2) to reduce latency for international manufacturing plants.
