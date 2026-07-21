# Deployment Architecture

The RATAN platform is designed for standard cloud-native deployment patterns, separating compute from stateful persistence.

## Infrastructure Diagram

```mermaid
graph TD
    Browser((Client Browser)) --> |HTTPS| Vercel[Next.js Application\n(Vercel / Cloudflare Pages)]
    
    Vercel --> |REST API| LoadBalancer[API Gateway / Load Balancer]
    
    LoadBalancer --> FastAPI1[FastAPI Node 1\n(Docker/K8s)]
    LoadBalancer --> FastAPI2[FastAPI Node 2\n(Docker/K8s)]
    
    subgraph Stateful Persistence
        FastAPI1 --> SQLite[(SQLite DB / Network Attached Storage)]
        FastAPI2 --> SQLite
    end
    
    subgraph Managed Cloud Services
        FastAPI1 --> Qdrant[(Qdrant Cloud Cluster)]
        FastAPI1 --> Backblaze[(Backblaze B2 Buckets)]
        
        FastAPI2 --> Qdrant
        FastAPI2 --> Backblaze
    end
    
    subgraph AI Inference
        FastAPI1 --> Groq[Groq Llama 3]
        FastAPI2 --> Gemini[Google Gemini]
    end
```

*(Note: While SQLite is currently utilized for rapid metadata deployment, production scaling beyond a single shared NAS volume would involve swapping the SQLite SQLAlchemy dialect for PostgreSQL.)*
