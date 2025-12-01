import os, uuid, asyncio, json, re
from typing import Any, Dict, List, Tuple
from pathlib import Path

from app.core.config import settings
from app.core.clients import get_opensearch, get_qdrant, get_logger
from sentence_transformers import SentenceTransformer
import requests
from unstructured.partition.pdf import partition_pdf
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

ROLE_HINTS = [
    "PRÜFUNGSSTELLE",
    "PRÜFUNGSAUSSCHUSS",
    "PRA",
    "STUDIERENDENBÜRO",
    "DEKANAT",
    "SENAT",
]

logger = get_logger(__name__)


def dehyphenize(text: str) -> str:
    # Soft-Hyphen entfernen und Silbentrennung über Zeilen umbrechen
    text = text.replace("\u00ad", "")  # Soft hyphen
    text = re.sub(r"-\n(\w)", r"\1", text)  # Trennstrich am Zeilenende
    return re.sub(r"[ \t]+\n", "\n", text)


def _meta_to_dict(meta: Any) -> Dict[str, Any]:
    if meta is None:
        return {}
    if isinstance(meta, dict):
        return meta
    # ElementMetadata etc.
    if hasattr(meta, "to_dict"):
        try:
            return meta.to_dict() or {}
        except Exception:
            pass
    # Fallback: zieh bekannte Felder per getattr
    out = {}
    for k in ("page_number", "section_title", "filename", "languages"):
        if hasattr(meta, k):
            out[k] = getattr(meta, k)
    return out


def extract_payload(el) -> dict:
    txt = getattr(el, "text", "") or ""
    roles = [
        w for w in re.findall(r"[A-ZÄÖÜ]{3,}(?:-[A-ZÄÖÜ]{2,})?", txt) if w in ROLE_HINTS
    ]

    raw_meta = getattr(el, "metadata", None)
    meta = _meta_to_dict(raw_meta)

    # Tabellenspezifische Metadaten extrahieren
    element_type = type(el).__name__
    table_html = None
    if element_type == "Table" and hasattr(el, "metadata"):
        # HTML-Repräsentation der Tabelle (falls vorhanden)
        table_html = getattr(el.metadata, "text_as_html", None)

    return {
        "page_number": meta.get("page_number"),
        "section_title": meta.get("section_title"),
        "roles": list(set(roles)),
        "element_type": element_type,
        "table_html": table_html,
    }


def _table_html_to_text(html: str) -> str:
    """Konvertiert HTML-Tabelle in lesbaren Text."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for tr in soup.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        rows.append(" | ".join(cells))
    return "\n".join(rows)


def parse_pdf(path: str) -> List[Tuple[str, dict]]:
    """PDF -> [(text, payload)] mit layout-/OCR-basiertem Chunking."""
    elements = partition_pdf(
        filename=str(path),
        strategy="hi_res",  # Layout-/OCR-Pipeline
        chunking_strategy="by_title",  # Titelgrenzen respektieren
        max_characters=settings.MAX_CHARACTERS,
        new_after_n_chars=settings.NEW_AFTER_N_CHARS,
        overlap=settings.OVERLAP,
        languages=settings.OCR_LANGUAGES.split(","),
        infer_table_structure=True,
        skip_infer_table_types=[],
    )
    chunks: List[Tuple[str, dict]] = []
    for el in elements:
        txt = dehyphenize(getattr(el, "text", "") or "")

        # Bei Tabellen: strukturierten Text bevorzugen
        element_type = type(el).__name__
        if element_type == "Table":
            logger.info("Table detected")
            # Falls HTML vorhanden, in Markdown-ähnlichen Text konvertieren
            html = getattr(getattr(el, "metadata", None), "text_as_html", None)
            if html:
                txt = _table_html_to_text(html) or txt

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


def index_chunks(
    doc_id: str,
    chunks: List[Tuple[str, dict]],
    *,
    process_name: str | None = None,
    tags: str | None = None,
    file_name: str | None = None,
):
    os_client = get_opensearch()
    qd = get_qdrant()

    texts = [t for t, _ in chunks]
    vectors = embed_texts(texts)

    for i, (t, meta) in enumerate(chunks):
        page = meta.get("page_number")

        # erweiterte Meta/Payload
        os_meta = {
            **meta,
            **({"process_name": process_name} if process_name else {}),
            **({"tags": tags} if tags else {}),
            **({"file_name": file_name} if file_name else {}),
        }

        # --- OpenSearch ---
        os_client.index(
            index=settings.OS_INDEX,
            id=f"{doc_id}:{i}",
            body={"document_id": doc_id, "text": t, "meta": os_meta},
        )

    # --- Qdrant ---
    from qdrant_client.http.models import PointStruct

    points = []
    for i, ((t, meta), v) in enumerate(zip(chunks, vectors)):

        payload = {
            "document_id": doc_id,
            "text": t,
            "chunk_id": f"{doc_id}:{i}",
            "process_name": process_name,
            "tags": tags,
            "file_name": file_name,
            **meta,
        }
        points.append(PointStruct(id=_uuid_for(doc_id, i), vector=v, payload=payload))
    qd.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)


def delete_all_chunks_opensearch() -> int:
    """
    Löscht ALLE Dokument-Chunks aus dem OpenSearch-Index.
    """
    os_client = get_opensearch()
    resp = os_client.delete_by_query(
        index=settings.OS_INDEX,
        body={"query": {"match_all": {}}},
    )
    return int(resp.get("deleted", 0))


def delete_chunks_by_process_opensearch(process_name: str) -> int:
    """
    Löscht alle Chunks mit meta.process_name == process_name aus OpenSearch.
    """
    os_client = get_opensearch()
    resp = os_client.delete_by_query(
        index=settings.OS_INDEX,
        body={"query": {"terms": {"meta.process_name.keyword": [process_name]}}},
    )
    return int(resp.get("deleted", 0))


def delete_all_chunks_qdrant() -> None:
    """
    Löscht ALLE Punkte aus der Qdrant-Collection.

    Implementiert als: Collection droppen und via ensure_indices() neu anlegen.
    """
    qd = get_qdrant()
    try:
        qd.delete_collection(settings.QDRANT_COLLECTION)
    except Exception:
        pass
    ensure_indices()


def delete_chunks_by_process_qdrant(process_name: str) -> None:
    """
    Löscht alle Punkte aus Qdrant, deren payload.process_name == process_name ist.
    """
    qd = get_qdrant()
    return qd.delete(
        collection_name=settings.QDRANT_COLLECTION,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="process_name",
                    match=MatchValue(value=process_name),
                )
            ]
        ),
    )


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
                process_name = fields.get("process_name", "")
                tags = fields.get("tags", "")
                file_name = fields.get("file_name", "")

                try:
                    if not p.exists():
                        raise FileNotFoundError(f"Upload file missing: {p}")
                    parsed = parse_pdf(
                        str(p)
                    )  # -> List[(text, payload)]  payload enthält page_number/section_title/roles
                    if parsed:
                        index_chunks(
                            doc_id,
                            parsed,
                            process_name=process_name,
                            tags=tags,
                            file_name=file_name,
                        )
                    await r.xadd(
                        "doc.indexed",
                        {
                            "document_id": doc_id,
                            "chunks": str(len(parsed)),
                            "tags": tags,
                            "process_name": process_name,
                        },
                    )
                    await r.xack(stream, group, msg_id)
                except Exception as e:
                    await r.xadd("doc.failed", {"document_id": doc_id, "error": str(e)})
                    await r.xack(stream, group, msg_id)
        await asyncio.sleep(0.1)
