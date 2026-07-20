# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

# Load environment variables FIRST before importing any internal modules
load_dotenv()

from app.api import health, documents, chat, stats, entities, cleanup, auth
# pyrefly: ignore [missing-import]
from fastapi.responses import JSONResponse
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(
    title="RATAN API",
    description="Retrieval-Augmented Technology for Asset Networks",
    version="1.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import time
from fastapi import Request

@app.middleware("http")
async def audit_log_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    
    # In production, we write this to `audit_logs` table via async tasks
    # For now, structured standard out
    logging.info(f"AUDIT | {request.method} {request.url.path} | Status: {response.status_code} | Latency: {process_time:.2f}ms | IP: {request.client.host}")
    
    response.headers["X-Process-Time"] = str(process_time)
    return response

from fastapi.exceptions import RequestValidationError
from app.exceptions import AppException, app_exception_handler, global_exception_handler

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request payload or parameters.",
                "details": exc.errors()
            }
        }
    )

# Include all API routers
app.include_router(health.router, prefix="", tags=["health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(stats.router, prefix="/api/v1/stats", tags=["stats"])
app.include_router(entities.router, prefix="/api/v1/entities", tags=["entities"])
app.include_router(cleanup.router, prefix="/api/v1/cleanup", tags=["cleanup"])

@app.api_route("/", methods=["GET", "HEAD"])
def read_root():
    return {"message": "Welcome to RATAN API"}
