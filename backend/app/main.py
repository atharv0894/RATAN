# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Request
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from fastapi.responses import JSONResponse, Response
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
import logging
import time

# Load environment variables FIRST before importing any internal modules
load_dotenv()

from app.api import (
    health, documents, chat, stats, entities, cleanup, auth,
    personal_auth, enterprise_auth, super_admin_auth, users,
    organizations, plants, departments, jobs, dashboard, admin,
    settings, admin_telemetry, personal_chat, personal_files,
    personal_memory, personal_google_auth
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://ratan-six.vercel.app",
    "https://ratan-agya0j0n1-atharv-shindes-projects.vercel.app",
    "https://ratan-uwno.onrender.com",
]

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "https://ratan-six.vercel.app",
    "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Max-Age": "86400",
}

app = FastAPI(
    title="RATAN API",
    description="Retrieval-Augmented Technology for Asset Networks",
    version="1.0.0"
)

# ─── Middleware Registration Order ────────────────────────────────────────────
# Starlette add_middleware() INSERTS at position 0 each time.
# LAST registered = position 0 = OUTERMOST = first to handle requests.
#
# Order of registration (inner → outer):
#   1. audit_log   (registered first → inner)
#   2. CORS        (registered second → outermost, runs first on every request)
# ─────────────────────────────────────────────────────────────────────────────

# Step 1: Inner middleware (registered first)
@app.middleware("http")
async def audit_log_middleware(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
    except Exception as exc:
        # Ensure unhandled exceptions still produce a response (with CORS headers added by outer middleware)
        logging.error(f"Unhandled exception in middleware: {exc}", exc_info=True)
        response = JSONResponse(
            status_code=500,
            content={"success": False, "error": {"code": "INTERNAL_ERROR", "message": "Unexpected server error."}},
        )
    process_time = (time.time() - start_time) * 1000
    logging.info(
        f"AUDIT | {request.method} {request.url.path} | "
        f"Status: {response.status_code} | Latency: {process_time:.2f}ms | "
        f"IP: {request.client.host if request.client else 'unknown'}"
    )
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Step 2: CORSMiddleware — outermost (registered last)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ─── Belt-and-suspenders: explicit OPTIONS handler ────────────────────────────
# If Starlette's CORSMiddleware ever fails to handle a preflight for any reason,
# this explicit route guarantees the browser always gets a 200 with CORS headers.
@app.options("/{full_path:path}")
async def global_options_handler(request: Request, full_path: str):
    origin = request.headers.get("origin", "https://ratan-six.vercel.app")
    allowed = origin if any(origin.endswith(d) for d in ["vercel.app", "onrender.com", "localhost:3000", "localhost:5173"]) else ALLOWED_ORIGINS[0]
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": allowed,
            "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "86400",
        },
    )

# ─── Exception Handlers ─────────────────────────────────────────────────────────
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

# ─── Routers ────────────────────────────────────────────────────────────────────
app.include_router(health.router, prefix="", tags=["health"])

# Authentication Routers
app.include_router(personal_auth.router, prefix="/api/v1/personal/auth", tags=["personal-auth"])
app.include_router(personal_google_auth.router, prefix="/api/v1/personal/auth", tags=["personal-google-auth"])
app.include_router(enterprise_auth.router, prefix="/api/v1/enterprise/auth", tags=["enterprise-auth"])
app.include_router(super_admin_auth.router, prefix="/api/v1/super-admin/auth", tags=["super-admin-auth"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["shared-auth"])

# Enterprise Routers
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
