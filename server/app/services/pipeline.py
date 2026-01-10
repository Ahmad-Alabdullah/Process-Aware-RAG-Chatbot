from enum import Enum
import os, uuid, asyncio, json, re
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

import numpy as np

from app.core.config import settings
from app.core.clients import get_opensearch, get_qdrant, get_logger
from sentence_transformers import SentenceTransformer
import requests
from unstructured.partition.pdf import partition_pdf
from qdrant_client.http.models import Filter, FieldCondition, MatchValue

logger = get_logger(__name__)


class ChunkingStrategy(str, Enum):
    BY_TITLE = "by_title"
    SEMANTIC = "semantic"
    SENTENCE_SEMANTIC = "sentence_semantic"  # LangChain SemanticChunker


ROLE_HINTS = [
    "PRÜFUNGSSTELLE",
    "PRÜFUNGSAUSSCHUSS",
    "PRA",
    "STUDIERENDENBÜRO",
    "DEKANAT",
    "SENAT",
]

SEMANTIC_BREAKPOINT_PERCENTILE = 95.0
SEMANTIC_MIN_CHUNK_CHARS = 100


def _get_index_names(strategy: ChunkingStrategy) -> Tuple[str, str]:
    """Gibt (os_index, qdrant_collection) basierend auf Strategie zurück."""
    if strategy == ChunkingStrategy.SEMANTIC:
        return settings.OS_SEMANTIC_INDEX, settings.QDRANT_SEMANTIC_COLLECTION
    if strategy == ChunkingStrategy.SENTENCE_SEMANTIC:
        return settings.OS_SEMANTIC_SENTENCE_QWEN3_INDEX, settings.QDRANT_SEMANTIC_SENTENCE_QWEN3_COLLECTION
    return settings.OS_INDEX, settings.QDRANT_COLLECTION


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
    """Extrahiert Payload aus Unstructured-Element."""
    meta = _meta_to_dict(getattr(el, "metadata", None))
    payload: Dict[str, Any] = {}

    if meta.get("page_number"):
        payload["page_number"] = meta["page_number"]
    if meta.get("section_title"):
        payload["section_title"] = meta["section_title"]

    element_type = type(el).__name__
    payload["element_type"] = element_type

    if element_type == "Table":
        html = getattr(getattr(el, "metadata", None), "text_as_html", None)
        if html:
            payload["table_html"] = html

    # Role extraction
    txt = (getattr(el, "text", "") or "").upper()
    roles = [r for r in ROLE_HINTS if r in txt]
    if roles:
        payload["roles"] = roles

    return payload


def _table_html_to_text(html: str) -> str:
    """Konvertiert HTML-Tabelle in lesbaren Text."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for tr in soup.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        rows.append(" | ".join(cells))
    return "\n".join(rows)


# ============================================================
# SEMANTIC CHUNKING (bge-m3 via Ollama)
# ============================================================


def _embed_for_chunking(texts: List[str]) -> np.ndarray:
    """
    Erstellt Embeddings für Semantic Chunking via bge-m3.
    bge-m3 ist optimiert für Satz-Ähnlichkeiten (im Gegensatz zu Query-Doc).
    """
    if not texts:
        return np.array([])

    try:
        resp = requests.post(
            f"{settings.OLLAMA_BASE}/api/embed",
            json={"model": "bge-m3:latest", "input": texts},
            timeout=120,
        )
        resp.raise_for_status()
        logger.info(f"bge-m3 Embeddings response: {resp}")
        return np.array(resp.json()["embeddings"])
    except Exception as e:
        logger.error(f"bge-m3 Embedding-Fehler: {e}")
        raise


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Berechnet Kosinus-Ähnlichkeit zwischen zwei Vektoren."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def _merge_metadata(metas: List[dict]) -> dict:
    """Merged Metadaten mehrerer Elemente zu einem Chunk."""
    if not metas:
        return {}
    if len(metas) == 1:
        return metas[0]

    merged = {}

    # page_number: Bereich (erste bis letzte Seite)
    pages = [m.get("page_number") for m in metas if m.get("page_number") is not None]
    if pages:
        if len(set(pages)) == 1:
            merged["page_number"] = pages[0]
        else:
            merged["page_number"] = f"{min(pages)}-{max(pages)}"

    # section_title: Erste gefundene
    for m in metas:
        if m.get("section_title"):
            merged["section_title"] = m["section_title"]
            break

    # element_type: "merged" wenn verschiedene Typen
    types = [m.get("element_type") for m in metas if m.get("element_type")]
    if types:
        merged["element_type"] = "merged" if len(set(types)) > 1 else types[0]

    # roles: Vereinigung aller gefundenen Rollen
    all_roles = []
    for m in metas:
        roles = m.get("roles", [])
        if isinstance(roles, list):
            all_roles.extend(roles)
    if all_roles:
        merged["roles"] = list(set(all_roles))

    # table_html: Erste gefundene Tabelle
    for m in metas:
        if m.get("table_html"):
            merged["table_html"] = m["table_html"]
            break

    return merged


def _semantic_chunk(
    elements: List[Any],
    max_chunk_chars: int = 2400,
) -> List[Tuple[str, dict]]:
    """
    Semantic Chunking mit Percentile-Methode (Greg Kamradt).

    Algorithmus:
    1. Extrahiere Text und Metadata aus jedem Element
    2. Berechne Embeddings für alle Elemente (bge-m3)
    3. Berechne paarweise Ähnlichkeiten zwischen aufeinanderfolgenden Elementen
    4. Finde Breakpoints bei großen Ähnlichkeits-Sprüngen (95. Percentile)
    5. Erstelle Chunks, respektiere max_chunk_chars

    Args:
        elements: Liste von Unstructured-Elementen
        max_chunk_chars: Maximale Chunk-Länge

    Returns:
        Liste von (text, metadata) Tupeln
    """
    if not elements:
        return []

    # 1. Texte und Metadaten extrahieren
    texts_raw: List[str] = []
    metas_raw: List[dict] = []

    for el in elements:
        txt = dehyphenize(getattr(el, "text", "") or "")
        if not txt.strip():
            continue

        # Tabellen-Handling
        element_type = type(el).__name__
        if element_type == "Table":
            html = getattr(getattr(el, "metadata", None), "text_as_html", None)
            if html:
                txt = _table_html_to_text(html) or txt

        texts_raw.append(txt)
        metas_raw.append(extract_payload(el))

    if len(texts_raw) == 0:
        return []

    if len(texts_raw) == 1:
        return [(texts_raw[0], metas_raw[0])]

    # 2. Embeddings berechnen (bge-m3)
    logger.info(
        f"Semantic Chunking: Berechne Embeddings für {len(texts_raw)} Elemente..."
    )
    embeddings = _embed_for_chunking(texts_raw)

    # 3. Paarweise Ähnlichkeiten berechnen
    similarities: List[float] = []
    for i in range(len(embeddings) - 1):
        sim = _cosine_similarity(embeddings[i], embeddings[i + 1])
        similarities.append(sim)

    logger.info(
        f"Similarities: min={min(similarities):.3f}, max={max(similarities):.3f}, "
        f"mean={np.mean(similarities):.3f}"
    )

    # 4. Breakpoints berechnen (Percentile-Methode)
    breakpoints = _compute_breakpoints_percentile(similarities)
    logger.info(
        f"Gefundene Breakpoints: {len(breakpoints)} bei Percentile {SEMANTIC_BREAKPOINT_PERCENTILE}%"
    )

    # 5. Chunks erstellen mit Längen-Limit
    chunks = _create_chunks_from_breakpoints(
        texts_raw, metas_raw, breakpoints, max_chunk_chars
    )

    logger.info(f"Semantic Chunking: {len(texts_raw)} Elemente → {len(chunks)} Chunks")
    return chunks


def _langchain_semantic_chunk(
    full_text: str,
    max_chunk_chars: int = 2400,
    breakpoint_threshold_type: str = "percentile",
    breakpoint_threshold_amount: float = 90.0,
) -> List[Tuple[str, dict]]:
    """
    LangChain SemanticChunker: Sentence-level semantic chunking.
    
    Verwendet langchain_experimental.text_splitter.SemanticChunker
    mit einem Ollama-basierten Embedding-Modell.
    
    Args:
        full_text: Gesamter Dokumenttext
        max_chunk_chars: Maximale Chunk-Länge (wird nachträglich angewendet)
        breakpoint_threshold_type: "percentile", "standard_deviation", oder "interquartile"
        breakpoint_threshold_amount: Threshold-Wert (z.B. 90 für 90. Percentile)
    
    Returns:
        Liste von (text, metadata) Tupeln
    """
    from langchain_experimental.text_splitter import SemanticChunker
    from langchain_ollama import OllamaEmbeddings
    
    if not full_text.strip():
        return []
    
    logger.info(
        f"LangChain Semantic Chunking: threshold={breakpoint_threshold_type}/{breakpoint_threshold_amount}"
    )
    
    # Ollama Embeddings für SemanticChunker
    embeddings = OllamaEmbeddings(
        model=settings.OLLAMA_EMBED_MODEL,
        base_url=settings.OLLAMA_BASE,
    )
    
    # SemanticChunker initialisieren
    text_splitter = SemanticChunker(
        embeddings=embeddings,
        breakpoint_threshold_type=breakpoint_threshold_type,
        breakpoint_threshold_amount=breakpoint_threshold_amount,
    )
    
    # Text in Chunks splitten
    docs = text_splitter.create_documents([full_text])
    
    # Chunks extrahieren und ggf. aufteilen wenn zu lang
    chunks: List[Tuple[str, dict]] = []
    for doc in docs:
        chunk_text = doc.page_content.strip()
        
        if len(chunk_text) < SEMANTIC_MIN_CHUNK_CHARS:
            continue
            
        if len(chunk_text) > max_chunk_chars:
            # Aufteilen bei max_chunk_chars
            for i in range(0, len(chunk_text), max_chunk_chars):
                sub_chunk = chunk_text[i:i + max_chunk_chars].strip()
                if len(sub_chunk) >= SEMANTIC_MIN_CHUNK_CHARS:
                    chunks.append((sub_chunk, {"chunking_strategy": "langchain_semantic"}))
        else:
            chunks.append((chunk_text, {"chunking_strategy": "langchain_semantic"}))
    
    logger.info(f"LangChain Semantic Chunking: {len(docs)} raw chunks → {len(chunks)} final chunks")
    return chunks


def _compute_breakpoints_percentile(similarities: List[float]) -> List[int]:
    """
    Greg Kamradt Methode: Breakpoints bei großen Ähnlichkeits-Sprüngen.

    Berechnet die Differenzen zwischen aufeinanderfolgenden Ähnlichkeiten
    und setzt Breakpoints dort, wo die Differenz über dem X. Percentile liegt.

    Returns:
        Liste von Indizes, an denen ein neuer Chunk beginnt (1-basiert)
    """
    if len(similarities) < 2:
        return []

    # Differenzen berechnen: Wie stark ändert sich die Ähnlichkeit?
    # Positiv = Ähnlichkeit sinkt (potenzieller Themenbruch)
    diffs: List[float] = []
    for i in range(len(similarities) - 1):
        diff = similarities[i] - similarities[i + 1]
        diffs.append(diff)

    # Threshold = 95. Percentile der Differenzen
    # Nur die obersten 5% der Sprünge werden Breakpoints
    threshold = float(np.percentile(diffs, SEMANTIC_BREAKPOINT_PERCENTILE))

    # Breakpoints = Stellen wo Differenz > Threshold
    # Index i in diffs bedeutet: Sprung zwischen Element i+1 und i+2
    # Also Breakpoint bei Element i+2
    breakpoints = [i + 2 for i, d in enumerate(diffs) if d > threshold]

    return breakpoints


def _create_chunks_from_breakpoints(
    texts: List[str],
    metas: List[dict],
    breakpoints: List[int],
    max_chunk_chars: int,
) -> List[Tuple[str, dict]]:
    """
    Erstellt Chunks basierend auf Breakpoints, respektiert max_chunk_chars.

    Wenn ein Chunk zu groß wird, wird er an der nächsten Element-Grenze geteilt.
    """
    chunks: List[Tuple[str, dict]] = []

    # Breakpoints um Start (0) und Ende (len) erweitern
    all_breaks = [0] + breakpoints + [len(texts)]

    for i in range(len(all_breaks) - 1):
        start = all_breaks[i]
        end = all_breaks[i + 1]

        segment_texts = texts[start:end]
        segment_metas = metas[start:end]

        # Prüfen ob Segment zu groß ist
        total_len = sum(len(t) for t in segment_texts)

        if total_len <= max_chunk_chars:
            # Segment passt → ein Chunk
            chunk_text = "\n\n".join(segment_texts)
            if len(chunk_text) >= SEMANTIC_MIN_CHUNK_CHARS:
                chunk_meta = _merge_metadata(segment_metas)
                chunks.append((chunk_text, chunk_meta))
        else:
            # Segment zu groß → aufteilen
            sub_chunks = _split_segment(segment_texts, segment_metas, max_chunk_chars)
            chunks.extend(sub_chunks)

    return chunks


def _split_segment(
    texts: List[str],
    metas: List[dict],
    max_chunk_chars: int,
) -> List[Tuple[str, dict]]:
    """Teilt ein zu großes Segment in kleinere Chunks."""
    chunks: List[Tuple[str, dict]] = []
    current_texts: List[str] = []
    current_metas: List[dict] = []
    current_len = 0

    for txt, meta in zip(texts, metas):
        txt_len = len(txt)

        # Prüfen ob Element noch in aktuellen Chunk passt
        # +2 für "\n\n" Separator
        separator_len = 2 if current_texts else 0

        if current_len + separator_len + txt_len > max_chunk_chars and current_texts:
            # Aktuellen Chunk abschließen
            chunk_text = "\n\n".join(current_texts)
            if len(chunk_text) >= SEMANTIC_MIN_CHUNK_CHARS:
                chunk_meta = _merge_metadata(current_metas)
                chunks.append((chunk_text, chunk_meta))

            # Neuen Chunk starten
            current_texts = []
            current_metas = []
            current_len = 0

        current_texts.append(txt)
        current_metas.append(meta)
        current_len += (separator_len + txt_len) if current_len > 0 else txt_len

    # Letzten Chunk hinzufügen
    if current_texts:
        chunk_text = "\n\n".join(current_texts)
        if len(chunk_text) >= SEMANTIC_MIN_CHUNK_CHARS:
            chunk_meta = _merge_metadata(current_metas)
            chunks.append((chunk_text, chunk_meta))

    return chunks


# ============================================================
# PARSE PDF (MIT STRATEGIE-AUSWAHL)
# ============================================================


def parse_pdf(
    path: str,
    strategy: ChunkingStrategy = ChunkingStrategy.BY_TITLE,
    max_characters: Optional[int] = None,
    overlap: Optional[int] = None,
) -> List[Tuple[str, dict]]:
    """
    PDF → [(text, payload)] mit konfigurierbarer Chunking-Strategie.

    Args:
        path: Pfad zur PDF-Datei
        strategy: BY_TITLE (default, 1800 chars) oder SEMANTIC (bge-m3)
        max_characters: Maximale Chunk-Länge (default: settings.MAX_CHARACTERS)
        overlap: Überlappung (nur bei BY_TITLE)

    Returns:
        Liste von (text, metadata) Tupeln
    """
    max_chars = max_characters or settings.MAX_CHARACTERS
    max_semantic_chars = settings.MAX_SEMANTIC_CHARACTERS
    ovl = overlap or settings.OVERLAP

    if strategy == ChunkingStrategy.SEMANTIC:
        # ============================================================
        # SEMANTIC CHUNKING
        # ============================================================
        logger.info(
            f"📄 Parsing mit SEMANTIC Chunking (bge-m3, percentile={SEMANTIC_BREAKPOINT_PERCENTILE}%, max={max_semantic_chars})"
        )

        elements = partition_pdf(
            filename=str(path),
            strategy="hi_res",
            chunking_strategy=None,
            languages=settings.OCR_LANGUAGES.split(","),
            infer_table_structure=True,
            skip_infer_table_types=[],
        )

        return _semantic_chunk(elements, max_chunk_chars=max_semantic_chars)

    elif strategy == ChunkingStrategy.SENTENCE_SEMANTIC:
        # ============================================================
        # SENTENCE-LEVEL SEMANTIC CHUNKING (LangChain SemanticChunker)
        # ============================================================
        logger.info(
            f"📄 Parsing mit SENTENCE_SEMANTIC Chunking (LangChain + Ollama, max={max_semantic_chars})"
        )

        # Erst Text extrahieren ohne Chunking
        elements = partition_pdf(
            filename=str(path),
            strategy="hi_res",
            chunking_strategy=None,
            languages=settings.OCR_LANGUAGES.split(","),
            infer_table_structure=True,
            skip_infer_table_types=[],
        )

        # Gesamten Text zusammenbauen
        full_text_parts = []
        for el in elements:
            txt = dehyphenize(getattr(el, "text", "") or "")
            element_type = type(el).__name__
            if element_type == "Table":
                html = getattr(getattr(el, "metadata", None), "text_as_html", None)
                if html:
                    txt = _table_html_to_text(html) or txt
            if txt.strip():
                full_text_parts.append(txt)
        
        full_text = "\n\n".join(full_text_parts)
        
        return _langchain_semantic_chunk(full_text, max_chunk_chars=max_semantic_chars)

    else:
        # ============================================================
        # BY_TITLE CHUNKING (Default)
        # ============================================================
        logger.info(
            f"📄 Parsing mit BY_TITLE Chunking (max={max_chars}, overlap={ovl})"
        )

        elements = partition_pdf(
            filename=str(path),
            strategy="hi_res",
            chunking_strategy="by_title",
            max_characters=max_chars,
            new_after_n_chars=settings.NEW_AFTER_N_CHARS,
            overlap=ovl,
            languages=settings.OCR_LANGUAGES.split(","),
            infer_table_structure=True,
            skip_infer_table_types=[],
        )

        chunks: List[Tuple[str, dict]] = []
        for el in elements:
            txt = dehyphenize(getattr(el, "text", "") or "")

            element_type = type(el).__name__
            if element_type == "Table":
                html = getattr(getattr(el, "metadata", None), "text_as_html", None)
                if html:
                    txt = _table_html_to_text(html) or txt

            if not txt.strip():
                continue

            payload = extract_payload(el)
            chunks.append((txt, payload))

        return chunks


# --- Embeddings backend ---
import threading
_embedding_lock = threading.Lock()  # Serialize GPU inference for thread-safety

_model = (
    SentenceTransformer(settings.EMBEDDING_MODEL)
    if settings.EMBEDDING_BACKEND == "hf"
    else None
)


def embed_texts(texts: List[str]) -> List[List[float]]:
    if settings.EMBEDDING_BACKEND == "hf":
        # Serialize GPU inference to prevent CUDA race conditions
        with _embedding_lock:
            return _model.encode(texts, normalize_embeddings=True).tolist()
    resp = requests.post(
        f"{settings.OLLAMA_BASE}/api/embed",
        json={"model": settings.OLLAMA_EMBED_MODEL, "input": texts},
    )
    resp.raise_for_status()
    return resp.json()["embeddings"]


# --- Indexing (OpenSearch + Qdrant) ---
def ensure_indices(strategy: ChunkingStrategy = ChunkingStrategy.BY_TITLE):
    os_index, qdrant_col = _get_index_names(strategy)

    os_client = get_opensearch()
    if not os_client.indices.exists(index=os_index):
        if strategy == ChunkingStrategy.SEMANTIC or strategy == ChunkingStrategy.SENTENCE_SEMANTIC:
            os_client.indices.create(
                index=os_index,
                body={
                    "mappings": {
                        "properties": {
                            "document_id": {"type": "keyword"},
                            "text": {"type": "text"},
                            "meta": {
                                "type": "object",
                                "properties": {
                                    "page_number": {"type": "keyword"},
                                    "section_title": {"type": "text"},
                                    "element_type": {"type": "keyword"},
                                    "process_name": {"type": "keyword"},
                                    "tags": {"type": "keyword"},
                                    "file_name": {"type": "keyword"},
                                    "roles": {"type": "keyword"},
                                    "table_html": {"type": "text", "index": False},
                                },
                            },
                        }
                    }
                },
            )
        else:
            # BY_TITLE: Flexibles Mapping (wie bisher)
            os_client.indices.create(
                index=os_index,
                body={
                    "mappings": {
                        "properties": {
                            "document_id": {"type": "keyword"},
                            "text": {"type": "text"},
                            "meta": {"type": "object", "enabled": True},
                        }
                    }
                },
            )

    # Qdrant-Collection anlegen
    from qdrant_client.http.models import VectorParams, Distance

    qd = get_qdrant()
    cols = [c.name for c in qd.get_collections().collections]
    if qdrant_col not in cols:
        dim = len(embed_texts(["probe"])[0])
        qd.create_collection(
            qdrant_col,
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
    strategy: ChunkingStrategy = ChunkingStrategy.BY_TITLE,
):
    os_index, qdrant_col = _get_index_names(strategy)

    os_client = get_opensearch()
    qd = get_qdrant()

    texts = [t for t, _ in chunks]
    vectors = embed_texts(texts)

    for i, (t, meta) in enumerate(chunks):

        # erweiterte Meta/Payload
        os_meta = {
            **meta,
            **({"process_name": process_name} if process_name else {}),
            **({"tags": tags} if tags else {}),
            **({"file_name": file_name} if file_name else {}),
        }

        # --- OpenSearch ---
        os_client.index(
            index=os_index,
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
    qd.upsert(collection_name=qdrant_col, points=points)


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


def delete_chunks_by_tag_opensearch(tag: str) -> int:
    """
    Löscht alle Chunks mit meta.tags == tag aus OpenSearch.
    """
    os_client = get_opensearch()
    resp = os_client.delete_by_query(
        index=settings.OS_INDEX,
        body={"query": {"terms": {"meta.tags.keyword": [tag]}}},
    )
    return int(resp.get("deleted", 0))


def delete_chunks_by_tag_qdrant(tag: str) -> None:
    """
    Löscht alle Punkte aus Qdrant, deren payload.tags == tag ist.
    """
    qd = get_qdrant()
    return qd.delete(
        collection_name=settings.QDRANT_COLLECTION,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="tags",
                    match=MatchValue(value=tag),
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

    ensure_indices(ChunkingStrategy.BY_TITLE)
    ensure_indices(ChunkingStrategy.SEMANTIC)
    ensure_indices(ChunkingStrategy.SENTENCE_SEMANTIC)

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
                strategy_str = fields.get("chunking_strategy", "by_title")
                try:
                    strategy = ChunkingStrategy(strategy_str)
                except ValueError:
                    strategy = ChunkingStrategy.BY_TITLE

                try:
                    if not p.exists():
                        raise FileNotFoundError(f"Upload file missing: {p}")
                    parsed = parse_pdf(
                        str(p), strategy=strategy
                    )  # -> List[(text, payload)]  payload enthält page_number/section_title/roles
                    if parsed:
                        index_chunks(
                            doc_id,
                            parsed,
                            process_name=process_name,
                            tags=tags,
                            file_name=file_name,
                            strategy=strategy,
                        )
                    await r.xadd(
                        "doc.indexed",
                        {
                            "document_id": doc_id,
                            "chunks": str(len(parsed)),
                            "tags": tags,
                            "process_name": process_name,
                            "chunking_strategy": strategy.value,
                        },
                    )
                    await r.xack(stream, group, msg_id)
                except Exception as e:
                    await r.xadd("doc.failed", {"document_id": doc_id, "error": str(e)})
                    await r.xack(stream, group, msg_id)
        await asyncio.sleep(0.1)
