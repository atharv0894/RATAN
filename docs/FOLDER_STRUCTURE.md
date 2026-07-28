# Folder Structure

RATAN is organized as a monorepo containing two decoupled projects: the Frontend (Next.js) and the Backend (FastAPI).

```text
RATAN/
├── README.md                 # Primary project documentation
├── docs/                     # Comprehensive architectural documentation
│   ├── ARCHITECTURE.md       # High-level overview
│   ├── FRONTEND.md           # Next.js & UI architecture
│   ├── BACKEND.md            # FastAPI patterns
│   ├── RAG_PIPELINE.md       # Full AI indexing and generation flow
│   ├── DATABASE_SCHEMA.md    # SQL schema and ER diagram
│   ├── API_REFERENCE.md      # API endpoints
│   ├── SECURITY.md           # Auth, RBAC, and data isolation
│   └── DEPLOYMENT.md         # CI/CD and env vars
│
├── frontend/                 # Next.js 14 Frontend Application
│   ├── app/                  # Next.js App Router (Pages & Layouts)
│   │   ├── dashboard/        # Enterprise Workspace Routes
│   │   ├── personal/         # Personal AI Workspace Routes
│   │   ├── super-admin/      # Admin Routes
│   │   ├── globals.css       # Tailwind CSS variables and base styles
│   │   ├── layout.tsx        # Root layout structure
│   │   └── page.tsx          # Landing page
│   ├── components/           # Reusable UI Elements
│   │   ├── admin/            # Admin-specific components
│   │   ├── dashboard/        # Enterprise-specific components
│   │   ├── layout/           # Sidebars, Navbars, Wrappers
│   │   └── ui/               # Generic UI components (buttons, inputs)
│   ├── lib/                  # Utilities
│   │   ├── api.ts            # Centralized Axios definitions
│   │   ├── auth-context.tsx  # React Context for JWT Auth
│   │   └── utils.ts          # Helper functions (cn for Tailwind, etc)
│   ├── public/               # Static assets (images, icons)
│   ├── types/                # TypeScript interface definitions
│   └── tailwind.config.ts    # Tailwind v4 configuration
│
└── backend/                  # FastAPI Backend Application
    ├── app/                  # Main Application Code
    │   ├── api/              # API Route Handlers
    │   │   ├── chat.py             # Enterprise Chat
    │   │   ├── personal_chat.py    # Personal Chat
    │   │   ├── documents.py        # Enterprise Documents
    │   │   ├── auth.py             # Shared Auth
    │   │   └── ...                 
    │   ├── database/         # Database Definitions
    │   │   ├── schema.py           # SQLite Schema Definitions
    │   │   └── sqlite.py           # Connection management
    │   ├── exceptions/       # Custom Exception Handling
    │   │   └── __init__.py         # Handlers mapped in main.py
    │   ├── rag/              # RAG Pipeline
    │   │   ├── rag_service.py      # Core RAG Orchestrator
    │   │   ├── qdrant_store.py     # Qdrant Vector DB Wrapper
    │   │   ├── embedding_service.py# FastEmbed BGE logic
    │   │   ├── prompt_builder.py   # LLM Prompt Construction
    │   │   └── search/             # Hybrid Search engine
    │   ├── services/         # Business Logic & Validation
    │   │   ├── auth_service.py     # JWT & Password Hashing
    │   │   ├── document_service.py # PDF Parsing & Storage
    │   │   ├── user_service.py     # User Management
    │   │   └── dependencies.py     # FastAPI Security Dependencies
    │   └── main.py           # Application Entrypoint & Middleware
    └── requirements.txt      # Python Dependencies
```
