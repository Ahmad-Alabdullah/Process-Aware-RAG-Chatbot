import os, uuid, asyncio, json, re
from typing import List, Tuple
from pathlib import Path

from app.core.config import settings
from app.core.clients import get_opensearch, get_qdrant
from sentence_transformers import SentenceTransformer
import requests
from unstructured.partition.pdf import partition_pdf

# =========================
# Chunking & OCR Parameter
# =========================
MAX_CHARS = int(os.environ.get("MAX_CHARACTERS", "1200"))
NEW_AFTER = int(os.environ.get("NEW_AFTER_N_CHARS", "900"))
OVERLAP = int(os.environ.get("OVERLAP", "150"))
OCR_LANGS = os.environ.get("OCR_LANGUAGES", "deu+eng")

ROLE_HINTS = [
    "PRÜFUNGSSTELLE",
    "PRÜFUNGSAUSSCHUSS",
    "PRA",
    "STUDIERENDENBÜRO",
    "DEKANAT",
    "SENAT",
]


def dehyphenize(text: str) -> str:
    # Soft-Hyphen entfernen und Silbentrennung über Zeilen umbrechen
    text = text.replace("\u00ad", "")  # Soft hyphen
    text = re.sub(r"-\n(\w)", r"\1", text)  # Trennstrich am Zeilenende
    return re.sub(r"[ \t]+\n", "\n", text)


def extract_payload(el) -> dict:
    meta = getattr(el, "metadata", {}) or {}
    txt = getattr(el, "text", "") or ""
    roles = [
        w for w in re.findall(r"[A-ZÄÖÜ]{3,}(?:-[A-ZÄÖÜ]{2,})?", txt) if w in ROLE_HINTS
    ]
    # Unstructured-Elemente tragen page_number/section_title in .metadata (ElementMetadata)
    page = (
        getattr(meta, "page_number", None)
        if hasattr(meta, "page_number")
        else meta.get("page_number")
    )
    sect = (
        getattr(meta, "section_title", None)
        if hasattr(meta, "section_title")
        else meta.get("section_title")
    )
    return {"page_number": page, "section_title": sect, "roles": list(set(roles))}


def parse_pdf(path: str) -> List[Tuple[str, dict]]:
    """PDF -> [(text, payload)] mit layout-/OCR-basiertem Chunking."""
    elements = partition_pdf(
        filename=str(path),
        strategy="hi_res",  # Layout-/OCR-Pipeline
        chunking_strategy="by_title",  # Titelgrenzen respektieren
        max_characters=MAX_CHARS,
        new_after_n_chars=NEW_AFTER,
        overlap=OVERLAP,
        coordinates=True,
        languages=OCR_LANGS.split("+"),
        infer_table_structure=True,
    )
    chunks: List[Tuple[str, dict]] = []
    for el in elements:
        txt = dehyphenize(getattr(el, "text", "") or "")
        if not txt.strip():
            continue
        payload = extract_payload(el)
        chunks.append((txt, payload))
    return chunks


# --- Embeddings backend ---
_model = (
    SentenceTransformer(settings.EMBEDDING_MODEL)
    if settings.EMBEDDING_BACKEND == "hf"
    else None
)


def embed_texts(texts: List[str]) -> List[List[float]]:
    if settings.EMBEDDING_BACKEND == "hf":
        return _model.encode(texts, normalize_embeddings=True).tolist()
    resp = requests.post(
        f"{settings.OLLAMA_BASE}/api/embed",
        json={"model": settings.OLLAMA_EMBED_MODEL, "input": texts},
    )
    resp.raise_for_status()
    return resp.json()["embeddings"]


# --- Indexing (OpenSearch + Qdrant) ---
def ensure_indices():
    os_client = get_opensearch()
    if not os_client.indices.exists(index=settings.OS_INDEX):
        os_client.indices.create(
            index=settings.OS_INDEX,
            body={
                "mappings": {
                    "properties": {
                        "document_id": {"type": "keyword"},
                        "text": {"type": "text"},
                        # meta bleibt flexibel für page_number/section_title/roles/coords/… (enabled=True)
                        "meta": {"type": "object", "enabled": True},
                    }
                }
            },
        )
    # Qdrant-Collection anlegen (Dimension via Probe bestimmen)
    from qdrant_client.http.models import VectorParams, Distance

    qd = get_qdrant()
    cols = [c.name for c in qd.get_collections().collections]
    if settings.QDRANT_COLLECTION not in cols:
        dim = len(embed_texts(["probe"])[0])
        qd.create_collection(
            settings.QDRANT_COLLECTION,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )


def _uuid_for(doc_id: str, i: int) -> str:
    from uuid import uuid5, NAMESPACE_URL

    return str(uuid5(NAMESPACE_URL, f"{doc_id}:{i}"))


def index_chunks(doc_id: str, chunks: List[Tuple[str, dict]]):
    os_client = get_opensearch()
    qd = get_qdrant()

    texts = [t for t, _ in chunks]
    vectors = embed_texts(texts)

    # OpenSearch
    for i, (t, meta) in enumerate(chunks):
        os_client.index(
            index=settings.OS_INDEX,
            id=f"{doc_id}:{i}",
            body={"document_id": doc_id, "text": t, "meta": meta},
        )

    # Qdrant
    from qdrant_client.http.models import PointStruct

    points = [
        PointStruct(
            id=_uuid_for(doc_id, i),
            vector=v,
            payload={
                "document_id": doc_id,
                "text": t,
                "chunk_id": f"{doc_id}:{i}",
                **meta,
            },
        )
        for i, ((t, meta), v) in enumerate(zip(chunks, vectors))
    ]
    qd.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)


# --- Background consumer (Redis Streams) ---
async def consume_uploads(r):
    """Liest aus Stream 'doc.uploaded' und führt parse+index aus."""
    stream = "doc.uploaded"
    group = "monolith"
    try:
        # "$" => create group at the end so the group receives only NEW messages.
        # "0" would make the group start from the beginning (whole history).
        await r.xgroup_create(stream, group, id="$", mkstream=True)
    except Exception:
        pass
    ensure_indices()

    while True:
        # ">" delivers new messages for the consumer group
        msgs = await r.xreadgroup(
            group, "api-1", streams={stream: ">"}, count=10, block=5000
        )
        if not msgs:
            continue
        for _, entries in msgs:
            for msg_id, fields in entries:
                doc_id = fields.get("document_id")
                p = Path(fields.get("path", "")).expanduser()
                try:
                    if not p.exists():
                        raise FileNotFoundError(f"Upload file missing: {p}")
                    parsed = parse_pdf(str(p))  # -> List[(text, payload)]
                    if parsed:
                        index_chunks(doc_id, parsed)  # payload in OS/Qdrant speichern
                    await r.xadd(
                        "doc.indexed",
                        {"document_id": doc_id, "chunks": str(len(parsed))},
                    )
                    await r.xack(stream, group, msg_id)
                except Exception as e:
                    await r.xadd("doc.failed", {"document_id": doc_id, "error": str(e)})
                    await r.xack(stream, group, msg_id)
        await asyncio.sleep(0.1)
