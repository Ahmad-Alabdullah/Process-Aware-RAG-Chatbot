from pathlib import Path
from typing import List, Literal
import os, uuid, shutil, json
import aiofiles
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.core.clients import get_redis
from app.services.pipeline import (
    ChunkingStrategy,
    delete_all_chunks_opensearch,
    delete_all_chunks_qdrant,
    delete_chunks_by_process_opensearch,
    delete_chunks_by_process_qdrant,
    delete_chunks_by_tag_opensearch,
    delete_chunks_by_tag_qdrant,
    ensure_indices,
    index_chunks,
)
from app.core.models.manualChunk import ManualChunk

router = APIRouter()

UPLOAD_DIR = Path("/server/data/tmp_uploads")


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    source: str = Form("manual"),
    tags: str = Form(""),
    process_name: str = Form(""),
    chunking_strategy: Literal["by_title", "semantic"] = Form("by_title"),
):
    """
    Upload und Verarbeitung von PDF-Dokumenten (async via Redis Stream).

    Args:
        file: Die hochzuladende PDF-Datei
        source: Quelle des Dokuments
        tags: Komma-separierte Tags
        process_name: Zugehöriger Prozessname
        chunking_strategy:
            - "by_title": Standard-Chunking nach Überschriften (1800 chars)
            - "semantic": Semantisches Chunking mit bge-m3 (Percentile 95%)
    """
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    doc_id = str(uuid.uuid4())
    dst = os.path.join(UPLOAD_DIR, f"{doc_id}-{file.filename}")

    async with aiofiles.open(dst, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            await out.write(chunk)

    r = get_redis()
    await r.xadd(
        "doc.uploaded",
        {
            "document_id": doc_id,
            "file_name": file.filename,
            "path": dst,
            "source": source,
            "tags": tags,
            "process_name": process_name,
            "chunking_strategy": chunking_strategy,
        },
    )

    return {
        "document_id": doc_id,
        "file_name": file.filename,
        "chunking_strategy": chunking_strategy,
        "status": "queued",
    }


@router.get("/documents")
async def list_documents():
    if not os.path.exists(UPLOAD_DIR):
        return []
    return [{"file": p} for p in os.listdir(UPLOAD_DIR)]


@router.delete("/all", summary="Alle Chunks in OS & Qdrant löschen")
def delete_all_chunks():
    deleted_os = delete_all_chunks_opensearch()
    delete_all_chunks_qdrant()
    return {
        "ok": True,
        "opensearch_deleted": deleted_os,
        "qdrant": "collection dropped & recreated",
    }


@router.delete(
    "/process/{process_name}",
    summary="Alle Chunks zu einem process_name in OS & Qdrant löschen",
)
def delete_chunks_by_process(process_name: str):
    if not process_name:
        raise HTTPException(status_code=400, detail="process_name darf nicht leer sein")

    deleted_os = delete_chunks_by_process_opensearch(process_name)
    delete_chunks_by_process_qdrant(process_name)

    return {
        "ok": True,
        "process_name": process_name,
        "opensearch_deleted": deleted_os,
        "qdrant": "delete by filter(process_name) requested",
    }


@router.delete(
    "/tag/{tag}",
    summary="Alle Chunks zu einem Tag in OS & Qdrant löschen",
)
def delete_chunks_by_tag(tag: str):
    if not tag:
        raise HTTPException(status_code=400, detail="tag darf nicht leer sein")

    deleted_os = delete_chunks_by_tag_opensearch(tag)
    delete_chunks_by_tag_qdrant(tag)

    return {
        "ok": True,
        "tag": tag,
        "opensearch_deleted": deleted_os,
        "qdrant": "delete by filter(tag) requested",
    }


@router.post("/chunks/manual")
def index_manual_chunks(chunks: List[ManualChunk]):
    """
    Manuelles Indexieren von Text-Chunks in OpenSearch + Qdrant.

    Jeder Eintrag entspricht genau einem Chunk (text + meta),
    der unter der angegebenen document_id gespeichert wird.
    """
    if not chunks:
        raise HTTPException(
            status_code=400, detail="Payload 'chunks' darf nicht leer sein."
        )

    ensure_indices(ChunkingStrategy.BY_TITLE)
    ensure_indices(ChunkingStrategy.SEMANTIC)

    indexed = 0
    for c in chunks:
        # pro Eintrag genau einen Chunk
        index_chunks(
            doc_id=c.document_id,
            chunks=[(c.text, c.meta)],
            process_name=c.process_name,
            tags=c.tags,
            strategy=c.chunking_strategy,
        )
        indexed += 1

    return {
        "ok": True,
        "indexed_chunks": indexed,
    }
