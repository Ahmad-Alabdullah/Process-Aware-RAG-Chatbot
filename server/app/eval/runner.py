from __future__ import annotations
import asyncio, yaml
from typing import Optional, Dict, Any, List
import typer
from pathlib import Path

from .config import RunConfig
from .db import (
    init_db,
    upsert_run,
    upsert_run_item,
    insert_retrieval_list,
    upsert_score,
    get_pool,
    upsert_gold_answers,
)
from .dataset import load_queries, load_qrels, load_answers_jsonl
from .clients.qa_client import QAClient
from .metrics.retrieval import compute_retrieval_metrics
from .metrics.generation import exact_match_f1, ais_heuristic
from .reporting import aggregate_and_store

app = typer.Typer(help="RAG Evaluation Runner")


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


def _confidence_from_resp(resp: Dict[str, Any]) -> float:
    if "confidence" in resp:
        try:
            return float(resp["confidence"])
        except Exception:
            pass
    try:
        lists = []
        if "retrieval" in resp:
            for key in ("ce", "rrf", "bm25", "dense"):
                arr = resp["retrieval"].get(key) or []
                if arr:
                    lists.append(arr)
        if lists:
            top = max(
                [
                    arr[0].get("score", 0.0)
                    for arr in lists
                    if arr and isinstance(arr[0].get("score", 0.0), (int, float))
                ]
                + [0.0]
            )
            import math

            return 1.0 / (1.0 + math.exp(-float(top)))
    except Exception:
        pass
    return 0.5


@app.command()
def run(config: str):
    """Execute a single run using the YAML config."""
    cfg = RunConfig(**yaml.safe_load(open(config, "r", encoding="utf-8").read()))
    run_id = upsert_run(cfg.run_name, config_json=cfg.model_dump())
    typer.echo(f"Run '{cfg.run_name}' -> id={run_id}")

    pool = get_pool()
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            "select id, query_id, text, process_name, process_id, roles "
            "from ragrun.queries where dataset_name=%s order by id",
            (cfg.dataset,),
        )
        rows = cur.fetchall()

    async def _exec_one(row):
        qpk, qid, text, pname, pid, roles = row
        payload = dict(cfg.qa_payload)
        payload.update(
            {"query": text, "processName": pname, "processId": pid, "roles": roles}
        )
        client = QAClient(cfg.qa_base_url)
        resp = await client.ask(payload)

        answer_text = resp.get("answer") or resp.get("output") or resp.get("text") or ""
        citations = resp.get("citations") or resp.get("sources") or []
        latency = resp.get("_latency_ms")
        token_in = resp.get("token_in")
        token_out = resp.get("token_out")
        whitelist_violation = bool(resp.get("whitelist_violation", False))
        decision = resp.get("decision", "answer")
        confidence = _confidence_from_resp(resp)

        upsert_run_item(
            run_id,
            qpk,
            {
                "status": "ok",
                "request_json": payload,
                "response_json": resp,
                "answer_text": answer_text,
                "citations": citations,
                "latency_ms": latency,
                "token_in": token_in,
                "token_out": token_out,
                "confidence": confidence,
                "whitelist_violation": whitelist_violation,
                "decision": decision,
            },
        )

        if isinstance(resp.get("retrieval"), dict):
            for key, arr in resp["retrieval"].items():
                if isinstance(arr, list):
                    rows_local = []
                    for i, it in enumerate(arr, start=1):
                        it2 = dict(it)
                        it2["rank"] = it.get("rank", i)
                        rows_local.append(it2)
                    insert_retrieval_list(run_id, qpk, key, rows_local)

    asyncio.run(asyncio.gather(*[_exec_one(r) for r in rows]))


@app.command()
def score(run_name: str):
    """Compute per-query metrics and aggregate them."""
    pool = get_pool()
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute("select id from ragrun.eval_runs where name=%s", (run_name,))
        row = cur.fetchone()
        if not row:
            raise typer.Exit(f"Run '{run_name}' not found.")
        run_id = row[0]

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

    for query_pk, answer_text, citations, *_ in items:
        with pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                "select chunk_id, relevance from ragrun.gold_evidence where query_pk=%s",
                (query_pk,),
            )
            g = cur.fetchall()
        gold = {chunk_id: int(rel) for chunk_id, rel in g}

        ranked = []
        with pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                select chunk_id from ragrun.retrieval_logs
                where run_id=%s and query_pk=%s and source in ('rrf','ce')
                order by source='rrf' desc, rank asc
                """,
                (run_id, query_pk),
            )
            ranked = [r[0] for r in cur.fetchall()]
        if not ranked:
            with pool.connection() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    select chunk_id from ragrun.retrieval_logs
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

        with pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                "select answers from ragrun.gold_answers where query_pk=%s", (query_pk,)
            )
            r = cur.fetchone()
        if r:
            gold_answers = [str(x) for x in (r[0] or [])]
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


if __name__ == "__main__":
    app()
