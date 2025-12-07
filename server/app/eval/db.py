from __future__ import annotations
import os, pathlib
from typing import Optional, Iterable, Dict, List, Any
from psycopg_pool import ConnectionPool
from psycopg2.extras import Json

DEFAULT_DSN = os.getenv(
    "EVAL_DB_DSN", "postgresql://postgres:postgres@localhost:5432/postgres"
)
_pool: Optional[ConnectionPool] = None


def get_pool(dsn: Optional[str] = None) -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            dsn or DEFAULT_DSN, min_size=1, max_size=10, max_idle=300
        )
    return _pool


def init_db(schema_path: str, dsn: Optional[str] = None) -> None:
    pool = get_pool(dsn)
    sql = pathlib.Path(schema_path).read_text(encoding="utf-8")
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(sql)
        conn.commit()


def upsert_run(name: str, config_json: dict, dsn: Optional[str] = None) -> int:
    pool = get_pool(dsn)
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            insert into ragrun.eval_runs (name, config_json)
            values (%s, %s)
            on conflict (name) do update set config_json = excluded.config_json
            returning id
            """,
            (name, config_json),
        )
        rid = cur.fetchone()[0]
        conn.commit()
        return rid


def upsert_query(
    dataset_name: str,
    query_id: str,
    text: str,
    process_name: Optional[str],
    process_id: Optional[str],
    roles: Optional[List[str]],
    current_node_id: Optional[str] = None,
    definition_id: Optional[str] = None,
    query_type: str = "mixed",
    expected_source: str = "both",
) -> int:
    pool = get_pool()
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            insert into ragrun.queries 
                (dataset_name, query_id, text, process_name, process_id, roles, 
                 current_node_id, definition_id, query_type, expected_source)
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            on conflict (dataset_name, query_id) do update
            set text = excluded.text,
                process_name = excluded.process_name,
                process_id = excluded.process_id,
                roles = excluded.roles,
                current_node_id = excluded.current_node_id,
                definition_id = excluded.definition_id,
                query_type = excluded.query_type,
                expected_source = excluded.expected_source
            returning id
            """,
            (
                dataset_name,
                query_id,
                text,
                process_name,
                process_id,
                roles,
                current_node_id,
                definition_id,
                query_type,
                expected_source,
            ),
        )
        conn.commit()
        return cur.fetchone()[0]


def insert_qrels(
    query_pk: int,
    qrels: Iterable[tuple[str, int]],
    document_ids: Optional[Dict[str, str]] = None,
) -> None:
    pool = get_pool()
    with pool.connection() as conn, conn.cursor() as cur:
        for chunk_id, rel in qrels:
            doc_id = (document_ids or {}).get(chunk_id)
            cur.execute(
                """
                insert into ragrun.gold_evidence (query_pk, chunk_id, document_id, relevance)
                values (%s, %s, %s, %s)
                on conflict (query_pk, chunk_id) do update set
                  relevance=excluded.relevance,
                  document_id=coalesce(excluded.document_id, ragrun.gold_evidence.document_id)
                """,
                (query_pk, chunk_id, doc_id, rel),
            )
        conn.commit()


def upsert_run_item(
    pool: ConnectionPool,
    run_id: int,
    query_id: str,
    answer_text: Optional[str],
    citations: Optional[list[Any]],
    latency_ms: Optional[float],
    status: str = "ok",
    error_message: Optional[str] = None,
    meta: Optional[dict[str, Any]] = None,
) -> None:
    """
    Speichert ein einzelnes QA-Resultat für eine Query.
    Schreibt konsistent in ragrun.eval_run_items (Evaluation-Log).
    """
    meta = meta or {}
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            insert into ragrun.eval_run_items (
                run_id,
                query_pk,
                status,
                request_json,
                response_json,
                answer_text,
                citations,
                latency_ms,
                token_in,
                token_out,
                confidence,
                whitelist_violation,
                decision
            )
            values (
                %(run_id)s,
                %(query_id)s,
                %(status)s,
                %(request_json)s,
                %(response_json)s,
                %(answer_text)s,
                %(citations)s,
                %(latency_ms)s,
                %(token_in)s,
                %(token_out)s,
                %(confidence)s,
                %(whitelist_violation)s,
                %(decision)s
            )
            on conflict (run_id, query_pk) do update set
                status             = excluded.status,
                request_json       = excluded.request_json,
                response_json      = excluded.response_json,
                answer_text        = excluded.answer_text,
                citations          = excluded.citations,
                latency_ms         = excluded.latency_ms,
                token_in           = excluded.token_in,
                token_out          = excluded.token_out,
                confidence         = excluded.confidence,
                whitelist_violation= excluded.whitelist_violation,
                decision           = excluded.decision
            """,
            {
                "run_id": run_id,
                "query_id": query_id,
                "status": status,
                "request_json": (
                    Json(meta.get("request"))
                    if meta.get("request") is not None
                    else None
                ),
                "response_json": (
                    Json(meta.get("response"))
                    if meta.get("response") is not None
                    else None
                ),
                "answer_text": answer_text,
                "citations": Json(citations) if citations is not None else None,
                "latency_ms": int(latency_ms) if latency_ms is not None else None,
                "token_in": meta.get("token_in"),
                "token_out": meta.get("token_out"),
                "confidence": meta.get("confidence"),
                "whitelist_violation": meta.get("whitelist_violation"),
                "decision": meta.get("decision"),
            },
        )
        conn.commit()


def insert_retrieval_list(
    run_id: int, query_pk: int, source: str, rows: list[dict]
) -> None:
    pool = get_pool()
    with pool.connection() as conn, conn.cursor() as cur:
        for r in rows:
            cur.execute(
                """
                insert into ragrun.retrieval_logs
                  (run_id, query_pk, rank, source, chunk_id, document_id, score, meta)
                values (%s,%s,%s,%s,%s,%s,%s,%s)
                on conflict (run_id, query_pk, rank, source) do update set
                  chunk_id=excluded.chunk_id,
                  document_id=excluded.document_id,
                  score=excluded.score,
                  meta=excluded.meta
                """,
                (
                    run_id,
                    query_pk,
                    r.get("rank"),
                    source,
                    r.get("chunk_id") or r.get("id") or r.get("chunkId"),
                    r.get("document_id") or r.get("doc_id"),
                    r.get("score"),
                    r,
                ),
            )
        conn.commit()


def upsert_score(
    run_id: int,
    query_pk: int,
    metric: str,
    value: float,
    details: Optional[dict] = None,
) -> None:
    pool = get_pool()
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            insert into ragrun.scores (run_id, query_pk, metric, value, details)
            values (%s,%s,%s,%s,%s)
            on conflict (run_id, query_pk, metric) do update set value=excluded.value, details=excluded.details
            """,
            (run_id, query_pk, metric, value, details),
        )
        conn.commit()


def upsert_aggregate(
    run_id: int,
    metric: str,
    value: float,
    n: int,
    ci: Optional[tuple[float, float]] = None,
) -> None:
    pool = get_pool()
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            insert into ragrun.aggregates (run_id, metric, value, n, ci_low, ci_high)
            values (%s,%s,%s,%s,%s,%s)
            on conflict (run_id, metric) do update set value=excluded.value, n=excluded.n, ci_low=excluded.ci_low, ci_high=excluded.ci_high
            """,
            (
                run_id,
                metric,
                value,
                n,
                (ci or (None, None))[0],
                (ci or (None, None))[1],
            ),
        )
        conn.commit()


def upsert_gold_answers(
    query_pk: int, answers: List[str], explanation: Optional[str]
) -> None:
    pool = get_pool()
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            insert into ragrun.gold_answers (query_pk, answers, explanation)
            values (%s, %s, %s)
            on conflict (query_pk) do update set answers=excluded.answers, explanation=excluded.explanation
            """,
            (query_pk, answers, explanation),
        )
        conn.commit()


def upsert_gold_gating(
    query_pk: int,
    expected_lane_ids: List[str],
    expected_node_ids: List[str],
    expected_lane_names: List[str],
    expected_task_names: List[str],
) -> None:
    """Speichert den erwarteten Gating-Kontext für eine PROCESS-Query."""
    pool = get_pool()
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            insert into ragrun.gold_gating 
                (query_pk, expected_lane_ids, expected_node_ids, 
                 expected_lane_names, expected_task_names)
            values (%s, %s, %s, %s, %s)
            on conflict (query_pk) do update set
                expected_lane_ids = excluded.expected_lane_ids,
                expected_node_ids = excluded.expected_node_ids,
                expected_lane_names = excluded.expected_lane_names,
                expected_task_names = excluded.expected_task_names
            """,
            (
                query_pk,
                expected_lane_ids,
                expected_node_ids,
                expected_lane_names,
                expected_task_names,
            ),
        )
        conn.commit()


def get_gold_gating(query_pk: int) -> Optional[Dict[str, List[str]]]:
    """Holt den erwarteten Gating-Kontext für eine Query."""
    pool = get_pool()
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            select expected_lane_ids, expected_node_ids, 
                   expected_lane_names, expected_task_names
            from ragrun.gold_gating
            where query_pk = %s
            """,
            (query_pk,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "expected_lane_ids": row[0] or [],
            "expected_node_ids": row[1] or [],
            "expected_lane_names": row[2] or [],
            "expected_task_names": row[3] or [],
        }


def upsert_retrieval_log(
    run_id: int,
    query_pk: int,
    chunk_id: str,
    rank: int,
    score: float,
    source: str = "rrf",
) -> None:
    """
    Speichert einen Retrieval-Log Eintrag.

    Args:
        run_id: ID des Evaluation-Runs
        query_pk: ID der Query
        chunk_id: ID des Chunks
        rank: Position im Ranking (1-indexed)
        score: Score (RRF oder Rerank)
        source: "rrf" (RRF-Fusion) oder "ce" (Cross-Encoder)
    """
    pool = get_pool()
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            insert into ragrun.retrieval_logs (run_id, query_pk, chunk_id, rank, score, source)
            values (%s, %s, %s, %s, %s, %s)
            on conflict (run_id, query_pk, chunk_id) do update
            set rank = excluded.rank, score = excluded.score, source = excluded.source
            """,
            (run_id, query_pk, chunk_id, rank, score, source),
        )
        conn.commit()
