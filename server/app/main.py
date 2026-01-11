from contextlib import asynccontextmanager
import contextlib
import asyncio, os
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.clients import get_redis, setup_logging
from app.core.auth import verify_api_key
from app.core.error_handlers import register_error_handlers, RequestIdMiddleware
from app.services.pipeline import consume_uploads
from app.routers import ingestion, search, qa, bpmn, whitelist

setup_logging(level="INFO")

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)

tags_metadata = [
    {"name": "ingestion", "description": "Dokumente hochladen & verwalten"},
    {"name": "search", "description": "Hybrid BM25 + Vector Suche"},
    {"name": "qa", "description": "Frage-Antwort über RAG/LLM"},
    {"name": "whitelist", "description": "Verwaltung der Whitelist für Prozesse"},
    {"name": "bpmn", "description": "BPMN 2.0 Prozess-Import und Verwaltung"},
]

bg_tasks = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    r = get_redis()
    # Background-Consumer für Upload -> Parse -> Index
    task = asyncio.create_task(consume_uploads(r))
    bg_tasks.append(task)
    yield
    # Shutdown
    for t in bg_tasks:
        t.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await t
    # Close Redis connection gracefully
    try:
        # get_redis() returns the shared client
        rc = get_redis()
        if rc:
            with contextlib.suppress(Exception):
                await rc.aclose()
    except Exception:
        pass


app = FastAPI(
    title="Process-Aware RAG API",
    version="0.0.1",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

# Add rate limiter to app state
app.state.limiter = limiter

# Register structured error handlers (replaces default slowapi handler)
register_error_handlers(app)

# Add request ID middleware for correlation
app.add_middleware(RequestIdMiddleware)

# Parse CORS origins from settings (comma-separated string)
cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-API-Key", "X-Request-ID"],
)

# Include routers with API key authentication dependency
api_key_dependency = [Depends(verify_api_key)]

app.include_router(ingestion.router, tags=[tags_metadata[0]["name"]], dependencies=api_key_dependency)
app.include_router(search.router, tags=[tags_metadata[1]["name"]], dependencies=api_key_dependency)
app.include_router(qa.router, tags=[tags_metadata[2]["name"]], dependencies=api_key_dependency)
app.include_router(whitelist.router, tags=[tags_metadata[3]["name"]], dependencies=api_key_dependency)
app.include_router(bpmn.router, tags=[tags_metadata[4]["name"]], dependencies=api_key_dependency)


@app.get("/health")
def health():
    """Health check endpoint - no authentication required."""
    return {"status": "ok"}

