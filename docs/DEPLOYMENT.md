# Deployment Guide

RATAN is designed to be deployed across modern serverless and PaaS platforms. 

## Infrastructure Overview

- **Frontend**: Vercel (Next.js)
- **Backend**: Render (FastAPI / Uvicorn)
- **Vector Database**: Qdrant (Qdrant Cloud)
- **Blob Storage**: Backblaze B2 (S3 API)
- **Database**: SQLite (locally/Render Disk) or PostgreSQL (Production)

## Environment Variables

### Backend (`backend/.env`)

**Security**
- `JWT_SECRET_KEY`: Secret key for JWT signing. (Required)
- `JWT_ALGORITHM`: Typically `HS256`. (Required)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Default `30`.
- `REFRESH_TOKEN_EXPIRE_DAYS`: Default `7`.

**Vector Database (Qdrant)**
- `QDRANT_URL`: The URL to your Qdrant cluster. Use `:memory:` for local dev.
- `QDRANT_API_KEY`: API Key for Qdrant Cloud.
- `QDRANT_TIMEOUT`: Default `30.0`.

**AI Providers**
- `GROQ_API_KEY`: API Key for Groq (Primary LLM).
- `GOOGLE_API_KEY`: API Key for Google Gemini (Fallback LLM).
- `GOOGLE_CLIENT_ID`: OAuth Client ID for frontend login.
- `GOOGLE_CLIENT_SECRET`: OAuth Client Secret.

**Storage (Backblaze B2)**
- `B2_APPLICATION_KEY_ID`: S3 Access Key.
- `B2_APPLICATION_KEY`: S3 Secret Key.
- `B2_BUCKET_NAME`: Name of the bucket.
- `B2_ENDPOINT`: Region endpoint (e.g., `s3.us-east-005.backblazeb2.com`).

### Frontend (`frontend/.env.local`)
- `NEXT_PUBLIC_API_URL`: The URL to the FastAPI backend (e.g., `https://ratan-uwno.onrender.com/api/v1`).
- `NEXT_PUBLIC_GOOGLE_CLIENT_ID`: OAuth Client ID for Google Login.

## Deployment Steps

### 1. Vector Database Setup
1. Create a cluster on [Qdrant Cloud](https://cloud.qdrant.io/).
2. Generate an API Key and copy the Cluster URL.
3. Add these to the backend environment variables.

### 2. Storage Setup
1. Create a Bucket in Backblaze B2.
2. Generate Application Keys with read/write access.
3. Note the S3 Endpoint.

### 3. Backend Deployment (Render)
1. Connect your GitHub repository to Render.
2. Create a new **Web Service**.
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Inject all Environment Variables.
6. (Optional) Attach a Persistent Disk if using SQLite, or connect a managed PostgreSQL instance.

### 4. Frontend Deployment (Vercel)
1. Import the repository into Vercel.
2. Set the **Framework Preset** to Next.js.
3. Set the **Root Directory** to `frontend`.
4. Inject `NEXT_PUBLIC_API_URL` pointing to your Render Web Service.
5. Deploy.

## CI/CD Pipeline
- Pull Requests to `main` trigger Vercel Preview Deployments.
- Merges to `main` trigger Render Auto-Deploy for the backend and Vercel Production Build for the frontend.
