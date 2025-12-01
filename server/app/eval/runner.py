from __future__ import annotations
import asyncio, yaml
from typing import Optional, Dict, Any, List, TypedDict, Literal
import typer
from pathlib import Path

from server.app.core.clients import get_logger

from .config import RunConfig
from .db import (
    init_db,
    upsert_run,
    upsert_run_item,
    insert_retrieval_list,
    upsert_score,
    get_pool,
    upsert_gold_answers,
    get_gold_gating,
)
from .dataset import load_queries, load_qrels, load_answers_jsonl
from .clients.qa_client import QAClient
from .metrics.retrieval import compute_retrieval_metrics
from .metrics.generation import exact_match_f1, ais_heuristic
from .metrics.gating import gating_recall, gating_precision
from .reporting import aggregate_and_store
from app.services.gating_context import (
    compute_gating_context,
    build_gating_hint_from_context,
    get_definition_id_for_process,
)

app = typer.Typer(help="RAG Evaluation Runner")

logger = get_logger(__name__)


@app.command()
def initdb(
    schema: str = "sql/schema.sql",
    dsn: Optional[str] = typer.Option(None, envvar="EVAL_DB_DSN"),
):
    """Create tables in Postgres."""
    init_db(schema, dsn)
    typer.echo("DB schema created.")


@app.command()
def load_dataset(dataset_name: str, queries_path: str, qrels_path: str):
    """Load queries and qrels into the DB."""
    qid_to_pk = load_queries(dataset_name, queries_path)
    load_qrels(dataset_name, qid_to_pk, qrels_path)
    typer.echo(f"Loaded dataset '{dataset_name}': {len(qid_to_pk)} queries.")


@app.command()
def load_answers(dataset_name: str, answers_path: str):
    """Load gold answers (optional, for EM/F1)."""
    pool = get_pool()
    qid_to_pk: Dict[str, int] = {}
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            "select id, query_id from ragrun.queries where dataset_name=%s",
            (dataset_name,),
        )
        for qpk, qid in cur.fetchall():
            qid_to_pk[qid] = qpk
    count = 0
    for qid, answers, explanation in load_answers_jsonl(answers_path):
        qpk = qid_to_pk.get(qid)
        if qpk:
            upsert_gold_answers(qpk, answers, explanation)
            count += 1
    typer.echo(f"Gold answers upserted for {count} queries.")


def _confidence_from_resp(resp: Dict[str, Any]) -> float | None:
    """
    Calculates confidence based on the best available signal.
    Priority: Explicit Confidence > Cross-Encoder (Logits) > Dense (Cosine) > None.
    """

    retrieval = resp.get("retrieval", {})
    if not isinstance(retrieval, dict):
        return None

    # 1. Cross-Encoder (CE): Beste Quelle für Wahrscheinlichkeiten
    # CE Scores sind Logits -> Sigmoid ist hier mathematisch korrekt.
    if "ce" in retrieval and retrieval["ce"]:
        top_item = retrieval["ce"][0]
        score = top_item.get("score")
        if isinstance(score, (int, float)):
            import math

            # Sigmoid: 1 / (1 + e^-x)
            return 1.0 / (1.0 + math.exp(-float(score)))

    # 2. Dense Retrieval: Kosinus-Ähnlichkeit ist meist 0..1
    # Wir nehmen den Wert direkt (geclippt auf 0..1 zur Sicherheit).
    if "dense" in retrieval and retrieval["dense"]:
        top_item = retrieval["dense"][0]
        score = top_item.get("score")
        if isinstance(score, (int, float)):
            return max(0.0, min(1.0, float(score)))

    # 3. BM25 / RRF: Keine Konfidenz berechnen
    # Diese Scores sind nicht normalisiert. Ein Fake-Wert ist irreführend.
    return None


async def _exec_one(row, cfg: RunConfig, run_id: int):
    """
    Führt eine einzelne Query aus und speichert das Ergebnis.
    """
    qpk = row["id"]
    qid = row["query_id"]
    text = row["text"]
    pname = row.get("process_name")
    pid = row.get("process_id")
    roles = row.get("roles") or []
    current_node_id = row.get("current_node_id")

    client = QAClient(base_url=cfg.qa_base_url)
    payload = dict(cfg.qa_payload)
    payload.update(
        {
            "query": text,
            "process_name": pname,
            "process_id": pid,
            "roles": roles,
            "current_node_id": current_node_id,  # An API weitergeben
        }
    )

    pool = get_pool()
    try:
        resp = await client.ask(payload)
        answer_text = resp.get("answer")
        citations = resp.get("context")
        latency_ms = float(resp.get("_latency_ms") or 0.0)
        decision = resp.get("decision")
        whitelist_violation = bool(resp.get("whitelist_violation"))

        # Gating Hint aus Response extrahieren
        gating_hint_from_response = resp.get("gating_hint")

        # Gating Context separat berechnen für Reproduzierbarkeit
        gating_context = None
        gating_hint_computed = None

        if pid or pname:
            # Definition-ID ermitteln falls nur process_name gegeben
            def_id = None
            if pname and not pid:
                def_id = get_definition_id_for_process(pname)

            gating_context = compute_gating_context(
                process_id=pid,
                definition_id=def_id,
                roles=roles,
                current_node_id=current_node_id,
            )
            gating_hint_computed = build_gating_hint_from_context(
                context=gating_context,
                process_name=pname,
                roles=roles,
            )

        # Meta-Informationen für spätere Analyse speichern
        meta = {
            "gating_hint": gating_hint_from_response,
            "gating_hint_computed": gating_hint_computed,
            "gating_context": gating_context,
            "prompt": resp.get("prompt"),
            "decision": decision,
            "whitelist_violation": whitelist_violation,
            "current_node_id": current_node_id,
        }

        upsert_run_item(
            pool,
            run_id,
            qid,
            answer_text,
            citations,
            latency_ms,
            status="ok",
            meta=meta,
        )

        logger.info(
            f"[Run {run_id}] Query {qid}: OK, latency={latency_ms:.0f}ms, "
            f"gating={'yes' if gating_hint_from_response else 'no'}"
        )

    except Exception as e:
        logger.error(f"[Run {run_id}] Query {qid} failed: {e}")
        upsert_run_item(
            pool,
            run_id,
            qid,
            answer_text=None,
            citations=None,
            latency_ms=0.0,
            status="error",
            meta={"error": str(e)},
        )


async def _run_all(
    rows: list[QueryRow], cfg: RunConfig, run_id: int, max_concurrency: int = 8
) -> None:
    sem = asyncio.Semaphore(max_concurrency)

    async def _wrapped(row: QueryRow) -> None:
        async with sem:
            await _exec_one(row, cfg, run_id)

    await asyncio.gather(*[_wrapped(r) for r in rows])


@app.command()
def run(
    config: str,
):
    """Execute a single run using the YAML config."""
    cfg = RunConfig(**yaml.safe_load(open(config, "r", encoding="utf-8").read()))
    run_id = upsert_run(cfg.run_name, config_json=cfg.model_dump())
    typer.echo(f"Run '{cfg.run_name}' -> id={run_id}")

    pool = get_pool()
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            select id, query_id, text, process_name, process_id, roles, current_node_id
            from ragrun.queries
            where dataset_name = %s
            """,
            (cfg.dataset,),
        )
        rows = [
            QueryRow(
                id=r[0],
                query_id=r[1],
                text=r[2],
                process_name=r[3],
                process_id=r[4],
                roles=r[5],
                current_node_id=r[6],
            )
            for r in cur.fetchall()
        ]

    asyncio.run(_run_all(rows, cfg, run_id, max_concurrency=cfg.max_concurrency or 8))


@app.command()
def score(run_name: str):
    """Compute per-query metrics and aggregate them."""
    pool = get_pool()
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            "select id, config_json from ragrun.eval_runs where name=%s", (run_name,)
        )
        row = cur.fetchone()
        if not row:
            raise typer.Exit(f"Run '{run_name}' not found.")
        run_id = row[0]
        cfg_json = row[1] or {}
    # RunConfig aus gespeicherter Config rekonstruieren (für Ranking-Optionen)
    cfg = RunConfig(**cfg_json)

    # 1. Alle Items holen
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            select i.query_pk, i.answer_text, i.citations, q.id, q.query_id, q.text
            from ragrun.eval_run_items i
            join ragrun.queries q on q.id = i.query_pk
            where i.run_id = %s
            """,
            (run_id,),
        )
        items = cur.fetchall()

    # FIX: Bulk Loading der Gold-Daten
    q_pks = tuple(i[0] for i in items)
    gold_map = {}
    gold_answers_map = {}

    if q_pks:
        with pool.connection() as conn, conn.cursor() as cur:
            # Gold Evidence laden
            cur.execute(
                "select query_pk, chunk_id, relevance from ragrun.gold_evidence where query_pk in %s",
                (q_pks,),
            )
            for qpk, cid, rel in cur.fetchall():
                if qpk not in gold_map:
                    gold_map[qpk] = {}
                gold_map[qpk][cid] = int(rel)

            # Gold Answers laden
            cur.execute(
                "select query_pk, answers from ragrun.gold_answers where query_pk in %s",
                (q_pks,),
            )
            for qpk, ans in cur.fetchall():
                gold_answers_map[qpk] = [str(x) for x in (ans or [])]

    for query_pk, answer_text, citations, *_ in items:
        gold = gold_map.get(query_pk, {})
        gold_answers = gold_answers_map.get(query_pk, [])

        ranked: list[str] = []
        sources = tuple(cfg.ranking_sources or [])
        if sources:
            with pool.connection() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    select chunk_id
                    from ragrun.retrieval_logs
                    where run_id=%s and query_pk=%s and source = any(%s)
                    order by
                        array_position(%s, source),  -- Reihenfolge wie in ranking_sources
                        rank asc
                    """,
                    (run_id, query_pk, sources, sources),
                )
                ranked = [r[0] for r in cur.fetchall()]

        if not ranked and cfg.ranking_fallback_all:
            with pool.connection() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    select chunk_id
                    from ragrun.retrieval_logs
                    where run_id=%s and query_pk=%s
                    order by rank asc
                    """,
                    (run_id, query_pk),
                )
                ranked = [r[0] for r in cur.fetchall()]

        if ranked and gold:
            m = compute_retrieval_metrics(ranked, gold, [3, 5, 10])
            for k, v in m.items():
                upsert_score(run_id, query_pk, k, float(v))

        em, f1 = exact_match_f1(answer_text or "", gold_answers)
        upsert_score(run_id, query_pk, "EM", float(em))
        upsert_score(run_id, query_pk, "F1", float(f1))

        cited_ids: List[str] = []
        if isinstance(citations, list):
            for c in citations:
                if isinstance(c, str):
                    cited_ids.append(c)
                elif isinstance(c, dict):
                    cid = c.get("chunk_id") or c.get("id") or c.get("chunkId")
                    if cid:
                        cited_ids.append(cid)
        ais = ais_heuristic(answer_text or "", cited_ids)
        upsert_score(run_id, query_pk, "AIS", float(ais))

        # NEU: Gating-Metriken für PROCESS-Queries
        gold_gating = get_gold_gating(query_pk)
        if gold_gating:
            # Gating-Kontext aus run_item.meta holen
            with pool.connection() as conn, conn.cursor() as cur:
                cur.execute(
                    "select meta from ragrun.eval_run_items where run_id=%s and query_pk=%s",
                    (run_id, query_pk),
                )
                row = cur.fetchone()
                meta = row[0] if row else {}

            predicted_context = meta.get("gating_context", {})

            # Recall: Wurden alle erwarteten Lanes/Nodes gefunden?
            recall_metrics = gating_recall(predicted_context, gold_gating)
            for metric, value in recall_metrics.items():
                upsert_score(run_id, query_pk, f"gating_{metric}", float(value))

            # Precision: Wurden nur relevante Lanes/Nodes verwendet?
            precision_metrics = gating_precision(predicted_context, gold_gating)
            for metric, value in precision_metrics.items():
                upsert_score(run_id, query_pk, f"gating_{metric}", float(value))

    report_path = aggregate_and_store(
        run_id,
        metrics=[
            "recall@3",
            "recall@5",
            "recall@10",
            "mrr@3",
            "mrr@5",
            "mrr@10",
            "ndcg@3",
            "ndcg@5",
            "ndcg@10",
            "EM",
            "F1",
            "AIS",
            "gating_lane_ids_recall",
            "gating_node_ids_recall",
            "gating_task_names_recall",
            "gating_avg_gating_recall",
            "gating_lane_ids_precision",
            "gating_node_ids_precision",
            "gating_task_names_precision",
            "gating_avg_gating_precision",
        ],
    )
    typer.echo(f"Scores computed. Report written to {report_path}")


@app.command()
def study(study_config: str, execute: bool = True, fractional: bool = False):
    """Run a plan of OFAT variants or a factorial spec."""
    plan = yaml.safe_load(open(study_config, "r", encoding="utf-8").read())
    baseline_path = plan["baseline"]
    base = RunConfig(
        **yaml.safe_load(open(baseline_path, "r", encoding="utf-8").read())
    )
    runs: List[RunConfig] = []

    if "variants" in plan:
        for v in plan["variants"]:
            name = v["name"]
            override = v["override"]
            cfg = base.model_copy(deep=True)
            if "dataset" in override:
                cfg.dataset = override["dataset"]
            if "qa_payload" in override:
                cfg.qa_payload.update(override["qa_payload"])
            if "factors" in override:
                f = override["factors"]
                for k, vv in f.items():
                    if isinstance(cfg.factors.get(k), dict) and isinstance(vv, dict):
                        cfg.factors[k].update(vv)
                    else:
                        cfg.factors[k] = vv
            cfg.run_name = name
            runs.append(cfg)
    elif "factors" in plan:
        import itertools

        grids = []
        keys = []
        for k, options in plan["factors"].items():
            keys.append(k)
            grids.append(options)
        combos = list(itertools.product(*grids))
        if plan.get("design") == "fractional":
            combos = combos[::2]
        for i, combo in enumerate(combos):
            cfg = base.model_copy(deep=True)
            run_name = f"FX_{i+1:03d}"
            for part in combo:
                if "dataset" in part:
                    cfg.dataset = part["dataset"]
                if "qa_payload" in part:
                    cfg.qa_payload.update(part["qa_payload"])
                if "factors" in part:
                    for kk, vv in part["factors"].items():
                        if isinstance(cfg.factors.get(kk), dict) and isinstance(
                            vv, dict
                        ):
                            cfg.factors[kk].update(vv)
                        else:
                            cfg.factors[kk] = vv
                if "qa_payload" in part and "model" in part["qa_payload"]:
                    run_name += "_" + str(part["qa_payload"]["model"]).split(":")[0]
                if "factors" in part and "rerank" in part["factors"]:
                    run_name += "_ce" + (
                        "ON" if part["factors"]["rerank"].get("ce") else "OFF"
                    )
                if "qa_payload" in part and "top_k" in part["qa_payload"]:
                    run_name += f"_k{part['qa_payload']['top_k']}"
                if (
                    "factors" in part
                    and "prompt" in part["factors"]
                    and part["factors"]["prompt"].get("repacking")
                ):
                    run_name += "_" + part["factors"]["prompt"]["repacking"]
            cfg.run_name = run_name
            runs.append(cfg)
    else:
        raise typer.Exit("Invalid study file. Provide either 'variants' or 'factors'.")

    out_dir = Path("generated_runs")
    out_dir.mkdir(exist_ok=True)
    for cfg in runs:
        path = out_dir / f"{cfg.run_name}.yaml"
        path.write_text(yaml.safe_dump(cfg.model_dump()), encoding="utf-8")
        typer.echo(f"Wrote {path}")
        if execute:
            run(str(path))
    typer.echo(f"Study executed with {len(runs)} runs.")


@app.command()
def compare(run_a: str, run_b: str, metric: str = "recall@5", iters: int = 2000):
    """Paired bootstrap comparison."""
    pool = get_pool()
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute("select id from ragrun.eval_runs where name=%s", (run_a,))
        ra = cur.fetchone()
        cur.execute("select id from ragrun.eval_runs where name=%s", (run_b,))
        rb = cur.fetchone()
    if not ra or not rb:
        raise typer.Exit("Run names not found.")
    from .stats import paired_bootstrap

    delta, pval, half = paired_bootstrap(ra[0], rb[0], metric=metric, iters=iters)
    typer.echo(
        f"Metric: {metric}\nΔ(mean)={delta:.4f} ±{half:.4f} (95% CI half-width)\np-value≈{pval:.4g}"
    )


class QueryRow(TypedDict):
    id: int
    query_id: str
    text: str
    process_name: str | None
    process_id: str | None
    roles: list[str] | None
    current_node_id: str | None


if __name__ == "__main__":
    app()
