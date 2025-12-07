from __future__ import annotations
import json
from typing import Iterable, Dict, Any, List, Optional

from app.core.clients import get_logger
from .db import upsert_query, insert_qrels, upsert_gold_gating

logger = get_logger(__name__)


def load_queries(dataset_name: str, path: str) -> Dict[str, int]:
    """
    Lädt Queries mit erweitertem Schema für H2-Evaluation.

    Feld: query_type
    - "structure": Nur Prozessstruktur (Gating-isoliert)
    - "knowledge": Nur Dokumentwissen (Retrieval-isoliert)
    - "mixed": Kombination aus beidem (realer Use-Case)
    """
    id_map: Dict[str, int] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            qid = obj["query_id"]
            text = obj["text"]

            p = obj.get("process_name")
            pid = obj.get("process_id")
            roles = obj.get("roles")
            current_node_id = obj.get("current_node_id")
            definition_id = obj.get("definition_id")

            query_type = obj.get("query_type", "mixed")  # Default: mixed
            expected_source = obj.get("expected_source", "both")

            qpk = upsert_query(
                dataset_name,
                qid,
                text,
                p,
                pid,
                roles,
                current_node_id,
                definition_id,
                query_type=query_type,
                expected_source=expected_source,
            )
            id_map[qid] = qpk
    return id_map


def load_qrels(dataset_name: str, qid_to_pk: Dict[str, int], path: str) -> None:
    """
    Lädt Qrels UND optionales Gating aus derselben JSONL-Datei.

    Format pro Zeile:
    {
      "query_id": "...",
      "chunk_id": "...",
      "relevance": 3,
      "gating": {  // optional, nur bei PROCESS-Queries
        "expected_lane_ids": [...],
        "expected_node_ids": [...],
        "expected_lane_names": [...],
        "expected_task_names": [...]
      }
    }
    """
    buf: Dict[int, List[tuple[str, int]]] = {}
    gating_buf: Dict[int, Dict[str, Any]] = {}
    unknown_queries = 0

    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            obj = json.loads(line)
            qid = obj["query_id"]

            if qid not in qid_to_pk:
                unknown_queries += 1
                logger.warning(
                    "QREL-Zeile %d referenziert unbekannte query_id=%s",
                    line_no,
                    qid,
                )
                continue

            qpk = qid_to_pk[qid]

            # Chunk-Relevanz verarbeiten
            chunk_id = obj.get("chunk_id")
            if chunk_id:
                rel_raw = obj.get("relevance", 1)
                try:
                    rel = int(rel_raw)
                except Exception:
                    logger.warning(
                        "QREL-Zeile %d: ungültiger relevance-Wert %r, fallback=1",
                        line_no,
                        rel_raw,
                    )
                    rel = 1
                rel = max(0, rel)  # Negative Werte auf 0 kappen
                buf.setdefault(qpk, []).append((chunk_id, rel))

            # Gating-Kontext verarbeiten (nur einmal pro Query)
            gating = obj.get("gating")
            if gating and qpk not in gating_buf:
                gating_buf[qpk] = gating

    # Qrels speichern
    for qpk, qrels in buf.items():
        insert_qrels(qpk, qrels)

    # Gating speichern
    for qpk, gating in gating_buf.items():
        upsert_gold_gating(
            query_pk=qpk,
            expected_lane_ids=gating.get("expected_lane_ids", []),
            expected_node_ids=gating.get("expected_node_ids", []),
            expected_lane_names=gating.get("expected_lane_names", []),
            expected_task_names=gating.get("expected_task_names", []),
        )

    logger.info(
        "load_qrels: %d Queries mit Chunks, %d mit Gating-Kontext",
        len(buf),
        len(gating_buf),
    )

    if unknown_queries:
        logger.warning(
            "load_qrels: %d QREL-Zeilen referenzierten unbekannte Queries.",
            unknown_queries,
        )


def load_answers_jsonl(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            yield obj["query_id"], obj.get("answers", []), obj.get("explanation")
