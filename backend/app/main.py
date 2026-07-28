# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

# Load environment variables FIRST before importing any internal modules
load_dotenv()

from app.api import health, documents, chat, stats, entities, cleanup, auth, personal_auth, enterprise_auth, super_admin_auth, users, organizations, plants, departments, jobs, dashboard, admin, settings, admin_telemetry, personal_chat, personal_files, personal_memory, personal_google_auth
# pyrefly: ignore [missing-import]
from fastapi.responses import JSONResponse
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(
    title="RATAN API",
    description="Retrieval-Augmented Technology for Asset Networks",
    version="1.0.0"
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
    logging.info(f"AUDIT | {request.method} {request.url.path} | Status: {response.status_code} | Latency: {process_time:.2f}ms | IP: {request.client.host if request.client else 'unknown'}")
    
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

# Important: In Starlette/FastAPI, the last middleware added is the outermost layer.
# CORSMiddleware must be the outermost layer so it intercepts OPTIONS requests before auth or audit logs.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://ratan-six.vercel.app",
        "https://ratan-agya0j0n1-atharv-shindes-projects.vercel.app",
        "https://ratan-uwno.onrender.com"
    ],
    allow_origin_regex="https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include all API routers
app.include_router(health.router, prefix="", tags=["health"])
# Authentication Routers (Strictly Separated)
app.include_router(personal_auth.router, prefix="/api/v1/personal/auth", tags=["personal-auth"])
app.include_router(personal_google_auth.router, prefix="/api/v1/personal/auth", tags=["personal-google-auth"])
app.include_router(enterprise_auth.router, prefix="/api/v1/enterprise/auth", tags=["enterprise-auth"])
app.include_router(super_admin_auth.router, prefix="/api/v1/super-admin/auth", tags=["super-admin-auth"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["shared-auth"])

app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(organizations.router, prefix="/api/v1/organizations", tags=["organizations"])
app.include_router(plants.router, prefix="/api/v1/plants", tags=["plants"])
app.include_router(departments.router, prefix="/api/v1/departments", tags=["departments"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(stats.router, prefix="/api/v1/stats", tags=["stats"])
app.include_router(entities.router, prefix="/api/v1/entities", tags=["entities"])
app.include_router(cleanup.router, prefix="/api/v1/cleanup", tags=["cleanup"])
app.include_router(settings.router, prefix="/api/v1/dashboard/system", tags=["settings"])
app.include_router(jobs.router, prefix="/api/v1/processing-jobs", tags=["processing-jobs"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(admin_telemetry.router, prefix="/api/v1/admin/telemetry", tags=["admin-telemetry"])

# Personal AI Routers
app.include_router(personal_chat.router, prefix="/api/v1/personal/chat", tags=["personal-chat"])
app.include_router(personal_files.router, prefix="/api/v1/personal/files", tags=["personal-files"])
app.include_router(personal_memory.router, prefix="/api/v1/personal/memory", tags=["personal-memory"])

@app.get("/")
def read_root():
    return {"message": "Welcome to RATAN API"}
