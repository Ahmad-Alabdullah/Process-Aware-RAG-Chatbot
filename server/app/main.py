from contextlib import asynccontextmanager
import contextlib
import asyncio, os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.clients import get_redis
from app.services.pipeline import consume_uploads
from app.routers import ingestion, search, qa
from app.routers import processes, state

tags_metadata = [
    {"name": "ingestion", "description": "Dokumente hochladen & verwalten"},
    {"name": "search", "description": "Hybrid BM25 + Vector Suche"},
    {"name": "qa", "description": "Frage-Antwort über RAG/LLM"},
    {"name": "processes", "description": "Prozessmodelle verwalten"},
    {"name": "state", "description": "Zustandsübergänge in Prozessen abfragen"},
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
    title="Process-Aware RAG (Monolith)",
    version="0.0.1",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

app.include_router(ingestion.router, prefix="/api", tags=["ingestion"])
app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(qa.router, prefix="/api", tags=["qa"])
app.include_router(processes.router, prefix="/api", tags=["processes"])
app.include_router(state.router, prefix="/api", tags=["state"])


@app.get("/", tags=["ingestion"])
def root():
    return {"service": "api", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
