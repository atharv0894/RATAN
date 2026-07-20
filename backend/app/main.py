# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

# Load environment variables FIRST before importing any internal modules
load_dotenv()

from app.api import health, documents, chat, stats, entities, cleanup
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

@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    logging.error(f"Unhandled Exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "An unexpected error occurred on the server.", "detail": str(exc)}
    )

# Include all API routers
app.include_router(health.router, prefix="", tags=["health"])
app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(stats.router, prefix="/stats", tags=["stats"])
app.include_router(entities.router, prefix="/entities", tags=["entities"])
app.include_router(cleanup.router, prefix="/cleanup", tags=["cleanup"])

@app.api_route("/", methods=["GET", "HEAD"])
def read_root():
    return {"message": "Welcome to RATAN API"}
