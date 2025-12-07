"""
Script zum Neu-Indexieren aller Dokumente mit einem anderen Embedding-Modell.

Struktur-Mapping:
  OpenSearch: process_name, tags, file_name in meta
  Qdrant: process_name, tags, file_name auf Top-Level

Verwendung:
    python -m app.eval.scripts.reindex --model qwen3-embedding --suffix qwen3
    python -m app.eval.scripts.reindex --model bge-m3 --suffix semantic --source-index chunks_semantic
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
from uuid import uuid5, NAMESPACE_URL

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.core.config import settings
from app.core.clients import get_opensearch, get_qdrant, get_logger, setup_logging
from app.services.pipeline import embed_texts

logger = get_logger(__name__)


def normalize_tags(tags: Any) -> str | None:
    """Normalisiert tags zu einem String."""
    if tags is None:
        return None
    if isinstance(tags, str):
        return tags if tags.strip() else None
    if isinstance(tags, list):
        return ",".join(str(t) for t in tags if t) or None
    return None


def normalize_page_number(page_number: Any, is_semantic_source: bool = False) -> Any:
    """
    Normalisiert page_number basierend auf Source-Index-Typ.

    Args:
        page_number: Der Wert aus dem Source-Index
        is_semantic_source: True wenn Source-Index semantic ist (page_number = String)

    Returns:
        - Bei semantic Source: Immer String ("1" oder "1-2")
        - Bei by_title Source: Original-Typ (meist int)
    """
    if page_number is None:
        return None

    if is_semantic_source:
        # Semantic Source: page_number ist bereits String ("1" oder "1-2")
        return str(page_number)
    else:
        # BY_TITLE Source: page_number ist int
        return page_number


def extract_from_os_hit(
    hit: Dict[str, Any], is_semantic_source: bool = False
) -> Dict[str, Any]:
    """
    Extrahiert alle relevanten Felder aus einem OpenSearch-Hit.

    Berücksichtigt die Struktur aus pipeline.py:
    - document_id, text auf Top-Level
    - process_name, tags, file_name, roles, page_number, etc. in meta

    Args:
        hit: OpenSearch-Hit
        is_semantic_source: True wenn Source-Index semantic ist
    """
    source = hit["_source"]
    chunk_id = hit["_id"]
    meta = source.get("meta", {})

    # Basis-Felder (Top-Level in OS)
    text = source.get("text", "")
    document_id = source.get("document_id", "")

    # Felder aus meta extrahieren
    process_name = meta.get("process_name")
    tags = normalize_tags(meta.get("tags"))
    file_name = meta.get("file_name")
    roles = meta.get("roles", [])

    # Weitere Meta-Felder
    page_number = normalize_page_number(meta.get("page_number"), is_semantic_source)
    section_title = meta.get("section_title")
    element_type = meta.get("element_type")
    table_html = meta.get("table_html")

    return {
        "chunk_id": chunk_id,
        "document_id": document_id,
        "text": text,
        # Felder für Qdrant Top-Level
        "process_name": process_name,
        "tags": tags,
        "file_name": file_name,
        # Felder für OS meta UND Qdrant payload spread
        "roles": roles,
        "page_number": page_number,
        "section_title": section_title,
        "element_type": element_type,
        "table_html": table_html,
    }


def _uuid_for(doc_id: str, i: int) -> str:
    """Gleiche UUID-Generierung"""
    return str(uuid5(NAMESPACE_URL, f"{doc_id}:{i}"))


def is_semantic_index(index_name: str) -> bool:
    """Prüft ob ein Index semantic ist (basierend auf Name oder Mapping)."""
    # Einfache Heuristik: Name enthält "semantic"
    if "semantic" in index_name.lower():
        return True

    # Alternativ: Mapping prüfen
    try:
        os_client = get_opensearch()
        mapping = os_client.indices.get_mapping(index=index_name)
        properties = mapping[index_name]["mappings"]["properties"]
        meta_props = properties.get("meta", {}).get("properties", {})

        # Semantic Index hat page_number als keyword
        page_number_type = meta_props.get("page_number", {}).get("type")
        return page_number_type == "keyword"
    except Exception:
        return False


def get_target_mapping(is_semantic_target: bool) -> Dict[str, Any]:
    """
    Gibt das korrekte Mapping für den Ziel-Index zurück.

    Args:
        is_semantic_target: True wenn Ziel-Index semantic-kompatibel sein soll
    """
    if is_semantic_target:
        # Semantic Mapping: page_number als keyword (String)
        return {
            "mappings": {
                "properties": {
                    "document_id": {"type": "keyword"},
                    "text": {"type": "text"},
                    "meta": {
                        "type": "object",
                        "properties": {
                            "page_number": {"type": "keyword"},  # String für "1-2"
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
        }
    else:
        # BY_TITLE Mapping: flexibles meta-Objekt
        return {
            "mappings": {
                "properties": {
                    "document_id": {"type": "keyword"},
                    "text": {"type": "text"},
                    "meta": {"type": "object", "enabled": True},
                }
            }
        }


def reindex_all_chunks(
    source_os_index: str,
    target_os_index: str,
    target_qdrant_collection: str,
    batch_size: int = 50,
    preserve_semantic_structure: bool = False,
) -> int:
    """
    Liest alle Chunks aus source_os_index und indexiert sie
    mit neuem Embedding in target_os_index + target_qdrant_collection.

    Args:
        source_os_index: Quell-Index
        target_os_index: Ziel-Index
        target_qdrant_collection: Ziel-Collection
        batch_size: Batch-Größe
        preserve_semantic_structure: True um semantic-Struktur zu erhalten (page_number als String)
    """
    os_client = get_opensearch()
    qd = get_qdrant()

    # Prüfen ob Source semantic ist
    is_semantic_source = is_semantic_index(source_os_index)
    logger.info(f"Source-Index '{source_os_index}' ist semantic: {is_semantic_source}")

    # Ziel-Struktur bestimmen
    is_semantic_target = preserve_semantic_structure or is_semantic_source
    logger.info(f"Ziel-Index '{target_os_index}' wird semantic: {is_semantic_target}")

    # 1. Ziel-OpenSearch-Index erstellen
    logger.info(f"Erstelle Ziel-Index: {target_os_index}")
    if not os_client.indices.exists(index=target_os_index):
        mapping = get_target_mapping(is_semantic_target)
        os_client.indices.create(index=target_os_index, body=mapping)
    else:
        logger.info(f"Ziel-Index {target_os_index} existiert bereits!")

    # 2. Ziel-Qdrant-Collection erstellen
    from qdrant_client.http.models import VectorParams, Distance, PointStruct

    cols = [c.name for c in qd.get_collections().collections]
    if target_qdrant_collection not in cols:
        probe_vec = embed_texts(["probe"])[0]
        dim = len(probe_vec)
        logger.info(
            f"Erstelle Qdrant Collection: {target_qdrant_collection} (dim={dim})"
        )
        qd.create_collection(
            target_qdrant_collection,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
    else:
        logger.info(f"Qdrant Collection {target_qdrant_collection} existiert bereits!")

    # 3. Alle Chunks aus Source lesen
    logger.info(f"Lese Chunks aus {source_os_index}...")

    scroll_response = os_client.search(
        index=source_os_index,
        body={"query": {"match_all": {}}, "size": batch_size},
        scroll="5m",
    )

    scroll_id = scroll_response["_scroll_id"]
    hits = scroll_response["hits"]["hits"]
    total = scroll_response["hits"]["total"]["value"]

    logger.info(f"Gefunden: {total} Chunks")

    processed = 0
    skipped = 0

    while hits:
        texts = []
        docs = []

        for hit in hits:
            try:
                doc = extract_from_os_hit(hit, is_semantic_source=is_semantic_source)

                if not doc["text"].strip():
                    logger.debug(f"Überspringe leeren Chunk: {doc['chunk_id']}")
                    skipped += 1
                    continue

                texts.append(doc["text"])
                docs.append(doc)

            except Exception as e:
                logger.info(f"Fehler bei Chunk {hit.get('_id')}: {e}")
                skipped += 1

        if texts:
            # Neue Embeddings erstellen
            try:
                vectors = embed_texts(texts)
            except Exception as e:
                logger.error(f"Embedding-Fehler für Batch: {e}")
                scroll_response = os_client.scroll(scroll_id=scroll_id, scroll="5m")
                scroll_id = scroll_response["_scroll_id"]
                hits = scroll_response["hits"]["hits"]
                continue

            # In OpenSearch indexieren
            for doc in docs:
                os_meta = {}

                if doc["process_name"]:
                    os_meta["process_name"] = doc["process_name"]
                if doc["tags"]:
                    os_meta["tags"] = doc["tags"]
                if doc["file_name"]:
                    os_meta["file_name"] = doc["file_name"]
                if doc["roles"]:
                    os_meta["roles"] = doc["roles"]
                if doc["page_number"] is not None:
                    # page_number beibehalten (String bei semantic, int bei by_title)
                    os_meta["page_number"] = doc["page_number"]
                if doc["section_title"]:
                    os_meta["section_title"] = doc["section_title"]
                if doc["element_type"]:
                    os_meta["element_type"] = doc["element_type"]
                if doc["table_html"]:
                    os_meta["table_html"] = doc["table_html"]

                os_client.index(
                    index=target_os_index,
                    id=doc["chunk_id"],
                    body={
                        "document_id": doc["document_id"],
                        "text": doc["text"],
                        "meta": os_meta,
                    },
                )

            # In Qdrant indexieren
            points = []
            for doc, vec in zip(docs, vectors):
                parts = doc["chunk_id"].rsplit(":", 1)
                doc_id = parts[0]
                idx = int(parts[1]) if len(parts) > 1 else 0

                payload = {
                    "document_id": doc["document_id"],
                    "text": doc["text"],
                    "chunk_id": doc["chunk_id"],
                    "process_name": doc["process_name"],
                    "tags": doc["tags"],
                    "file_name": doc["file_name"],
                }

                if doc["roles"]:
                    payload["roles"] = doc["roles"]
                if doc["page_number"] is not None:
                    payload["page_number"] = doc["page_number"]
                if doc["section_title"]:
                    payload["section_title"] = doc["section_title"]
                if doc["element_type"]:
                    payload["element_type"] = doc["element_type"]
                if doc["table_html"]:
                    payload["table_html"] = doc["table_html"]

                points.append(
                    PointStruct(
                        id=_uuid_for(doc_id, idx),
                        vector=vec,
                        payload=payload,
                    )
                )

            qd.upsert(collection_name=target_qdrant_collection, points=points)
            processed += len(docs)

        # Fortschritt loggen
        if processed % 100 == 0 or not hits:
            logger.info(f"Verarbeitet: {processed}/{total} (übersprungen: {skipped})")

        # Nächste Batch
        scroll_response = os_client.scroll(scroll_id=scroll_id, scroll="5m")
        scroll_id = scroll_response["_scroll_id"]
        hits = scroll_response["hits"]["hits"]

    # Scroll-Kontext freigeben
    try:
        os_client.clear_scroll(scroll_id=scroll_id)
    except Exception:
        pass

    logger.info(f"Fertig! {processed} Chunks indexiert, {skipped} übersprungen.")
    return processed


def main():
    parser = argparse.ArgumentParser(
        description="Re-index chunks with different embedding model"
    )
    parser.add_argument(
        "--model", required=True, help="Embedding model (e.g., qwen3-embedding, bge-m3)"
    )
    parser.add_argument(
        "--suffix", required=True, help="Suffix for new index/collection (e.g., qwen3)"
    )
    parser.add_argument(
        "--source-index",
        default="chunks",
        help="Source OpenSearch index (default: chunks)",
    )
    parser.add_argument(
        "--batch-size", type=int, default=50, help="Batch size (default: 50)"
    )
    parser.add_argument(
        "--backend",
        default="ollama",
        choices=["ollama", "hf"],
        help="Embedding backend (default: ollama)",
    )
    parser.add_argument(
        "--preserve-semantic",
        action="store_true",
        help="Force semantic structure in target (page_number as string)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Only show stats, don't reindex"
    )

    args = parser.parse_args()

    # Embedding-Modell überschreiben
    os.environ["EMBEDDING_BACKEND"] = args.backend
    if args.backend == "ollama":
        os.environ["OLLAMA_EMBED_MODEL"] = args.model
    else:
        os.environ["EMBEDDING_MODEL"] = args.model

    target_os = f"{args.source_index}_{args.suffix}"
    target_qd = f"{args.source_index}_{args.suffix}"

    # Semantic-Status ermitteln
    is_semantic_source = is_semantic_index(args.source_index)

    logger.info("=" * 60)
    logger.info("REINDEX SCRIPT")
    logger.info("=" * 60)
    logger.info(f"Model: {args.model} (Backend: {args.backend})")
    logger.info(f"Source: {args.source_index} (semantic: {is_semantic_source})")
    logger.info(f"Target: {target_os} / {target_qd}")
    logger.info(
        f"Preserve semantic structure: {args.preserve_semantic or is_semantic_source}"
    )
    logger.info("=" * 60)

    if args.dry_run:
        os_client = get_opensearch()
        count = os_client.count(index=args.source_index)["count"]
        logger.info(f"DRY RUN: Würde {count} Chunks re-indexieren")
        return

    reindex_all_chunks(
        source_os_index=args.source_index,
        target_os_index=target_os,
        target_qdrant_collection=target_qd,
        batch_size=args.batch_size,
        preserve_semantic_structure=args.preserve_semantic,
    )


if __name__ == "__main__":
    setup_logging(level="INFO")
    main()
