from pathlib import Path
from typing import List
import os, uuid, shutil, json
import aiofiles
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.core.clients import get_redis
from app.services.pipeline import (
    delete_all_chunks_opensearch,
    delete_all_chunks_qdrant,
    delete_chunks_by_process_opensearch,
    delete_chunks_by_process_qdrant,
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
):
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
        },
    )
    return {
        "document_id": doc_id,
        "file_name": file.filename,
        "path": dst,
        "tags": tags,
        "process_name": process_name,
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

    ensure_indices()

    indexed = 0
    for c in chunks:
        # pro Eintrag genau einen Chunk
        index_chunks(
            doc_id=c.document_id,
            chunks=[(c.text, c.meta)],
            process_name=c.process_name,
            tags=c.tags,
        )
        indexed += 1

    return {
        "ok": True,
        "indexed_chunks": indexed,
    }
