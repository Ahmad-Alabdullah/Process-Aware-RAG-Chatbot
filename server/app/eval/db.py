from __future__ import annotations
import os, pathlib
from typing import Optional, Iterable, Dict, List
from psycopg_pool import ConnectionPool

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
) -> int:
    pool = get_pool()
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            insert into ragrun.queries (dataset_name, query_id, text, process_name, process_id, roles)
            values (%s, %s, %s, %s, %s, %s)
            on conflict (dataset_name, query_id) do update set
              text=excluded.text, process_name=excluded.process_name, process_id=excluded.process_id, roles=excluded.roles
            returning id
            """,
            (dataset_name, query_id, text, process_name, process_id, roles),
        )
        qpk = cur.fetchone()[0]
        conn.commit()
        return qpk


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


def upsert_run_item(run_id: int, query_pk: int, item: dict) -> None:
    pool = get_pool()
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            insert into ragrun.eval_run_items
              (run_id, query_pk, status, request_json, response_json, answer_text,
               citations, latency_ms, token_in, token_out, confidence, whitelist_violation, decision)
            values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            on conflict (run_id, query_pk) do update set
              status=excluded.status,
              request_json=excluded.request_json,
              response_json=excluded.response_json,
              answer_text=excluded.answer_text,
              citations=excluded.citations,
              latency_ms=excluded.latency_ms,
              token_in=excluded.token_in,
              token_out=excluded.token_out,
              confidence=excluded.confidence,
              whitelist_violation=excluded.whitelist_violation,
              decision=excluded.decision
            """,
            (
                run_id,
                query_pk,
                item.get("status", "ok"),
                item.get("request_json"),
                item.get("response_json"),
                item.get("answer_text"),
                item.get("citations"),
                item.get("latency_ms"),
                item.get("token_in"),
                item.get("token_out"),
                item.get("confidence"),
                item.get("whitelist_violation"),
                item.get("decision"),
            ),
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
