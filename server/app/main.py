from contextlib import asynccontextmanager
import contextlib
import asyncio, os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.clients import get_redis, setup_logging
from app.services.pipeline import consume_uploads
from app.routers import ingestion, search, qa, bpmn, whitelist

setup_logging(level="INFO")

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingestion.router, tags=[tags_metadata[0]["name"]])
app.include_router(search.router, tags=[tags_metadata[1]["name"]])
app.include_router(qa.router, tags=[tags_metadata[2]["name"]])
app.include_router(whitelist.router, tags=[tags_metadata[3]["name"]])
app.include_router(bpmn.router, tags=[tags_metadata[4]["name"]])


@app.get("/health")
def health():
    return {"status": "ok"}
