from __future__ import annotations
import asyncio, yaml
from typing import Optional, Dict, Any, List, TypedDict
import typer
import httpx
from pathlib import Path
from app.core.clients import get_logger, setup_logging
from app.eval.metrics.faithfulness import compute_faithfulness_metrics
from app.eval.metrics.llm_judge import (
    judge_factual_consistency,
    judge_answer_relevance,
    judge_context_relevance,
    judge_faithfulness,
)

from .config import RunConfig
from .db import (
    init_db,
    upsert_retrieval_log,
    upsert_run,
    upsert_run_item,
    upsert_score,
    get_pool,
    upsert_gold_answers,
    get_gold_gating,
)
from .dataset import load_queries, load_qrels, load_answers_jsonl
from .clients.qa_client import QAClient
from .metrics.retrieval import compute_retrieval_metrics
from .metrics.generation import (
    compute_generation_metrics,
)
from .metrics.gating import gating_recall, gating_precision
from .reporting import METRIC_GROUPS, aggregate_and_store

app = typer.Typer(help="RAG Evaluation Runner")

logger = get_logger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"


def _unload_ollama_model(model: str, base_url: str = OLLAMA_BASE_URL) -> bool:
    """
    Unloads a specific Ollama model from VRAM by sending keep_alive=0.
    """
    try:
        resp = httpx.post(
            f"{base_url}/api/generate",
            json={"model": model, "prompt": "", "keep_alive": 0},
            timeout=60.0,
        )
        return resp.status_code == 200
    except Exception as e:
        logger.warning(f"Could not unload model '{model}': {e}")
        return False


def _unload_all_ollama_models(base_url: str = OLLAMA_BASE_URL) -> int:
    """
    Unloads ALL currently loaded Ollama models from VRAM.
    
    Uses /api/ps to get list of loaded models, then unloads each one.
    Returns the number of models unloaded.
    """
    import time
    
    try:
        # Get list of currently loaded models
        resp = httpx.get(f"{base_url}/api/ps", timeout=10.0)
        if resp.status_code != 200:
            logger.warning(f"Could not get loaded models: {resp.status_code}")
            return 0
        
        data = resp.json()
        models = data.get("models", [])
        
        if not models:
            logger.info("No models currently loaded in VRAM")
            return 0
        
        unloaded = 0
        for model_info in models:
            model_name = model_info.get("name", model_info.get("model"))
            if model_name:
                logger.info(f"Unloading model '{model_name}' from VRAM...")
                if _unload_ollama_model(model_name, base_url):
                    unloaded += 1
        
        if unloaded > 0:
            logger.info(f"Unloaded {unloaded} models. Waiting for VRAM to free...")
            time.sleep(60)
        
        return unloaded
        
    except Exception as e:
        logger.warning(f"Could not unload models: {e}")
        return 0


def _get_model_from_config(cfg: RunConfig) -> str:
    """Extract the QA model name from config."""
    # Check factors.llm.qa.model first
    llm_cfg = cfg.factors.get("llm", {})
    qa_cfg = llm_cfg.get("qa", {})
    if qa_cfg.get("model"):
        return qa_cfg["model"]
    # Fallback to qa_payload.model
    return cfg.qa_payload.get("model", "qwen3:8b")


@app.command()
def initdb(
    schema: str = "db/init/schema.sql",
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


def _extract_predicted_gating(gating_metadata: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Extrahiert die tatsächlich verwendeten Gating-Elemente aus der Response-Metadata.
    """
    # Sets für automatische Deduplizierung
    lane_ids: set[str] = set()
    node_ids: set[str] = set()
    task_names: set[str] = set()

    if not gating_metadata:
        return {"lane_ids": [], "node_ids": [], "task_names": []}

    # Direkte Felder
    if "allowed_lane_ids" in gating_metadata:
        lane_ids.update(gating_metadata["allowed_lane_ids"])
    if "allowed_node_ids" in gating_metadata:
        node_ids.update(gating_metadata["allowed_node_ids"])
    if "allowed_task_names" in gating_metadata:
        task_names.update(gating_metadata["allowed_task_names"])

    # Aus allowed_lanes extrahieren
    for lane in gating_metadata.get("allowed_lanes", []):
        if isinstance(lane, dict) and lane.get("id"):
            lane_ids.add(lane["id"])
        elif isinstance(lane, str):
            lane_ids.add(lane)

    # Aus allowed_nodes extrahieren
    for node in gating_metadata.get("allowed_nodes", []):
        if isinstance(node, dict):
            if node.get("id"):
                node_ids.add(node["id"])
            if node.get("name"):
                task_names.add(node["name"])
        elif isinstance(node, str):
            node_ids.add(node)

    return {
        "lane_ids": list(lane_ids),
        "node_ids": list(node_ids),
        "task_names": list(task_names),
    }


async def _call_one(qr: QueryRow, client: QAClient, cfg: RunConfig, run_id: int):
    """Einzelner API-Call mit Logging."""
    # Embedding-Config aus factors
    emb_cfg = cfg.get_embedding_config()
    rerank_cfg = cfg.get_rerank_config()
    os_index, qdrant_collection = cfg.get_index_names()

    payload = {
        **cfg.qa_payload,
        "query": qr["text"],
        "process_name": qr["process_name"],
        "process_id": qr["process_id"],
        "roles": qr["roles"] or [],
        "current_node_id": qr["current_node_id"],
        "definition_id": qr["definition_id"],
    }

    # Reranking
    if rerank_cfg.enabled:
        payload["use_rerank"] = True
        payload["rerank_top_n"] = rerank_cfg.top_n
    else:
        payload["use_rerank"] = payload.get("use_rerank", False)

    # Query-Parameter für Embedding-Config
    query_params = {
        "os_index": os_index,
        "qdrant_collection": qdrant_collection,
        "embedding_backend": emb_cfg.backend,
        "embedding_model": emb_cfg.model,
    }

    t0 = asyncio.get_event_loop().time()
    resp = await client.ask(payload, query_params=query_params)
    latency = int((asyncio.get_event_loop().time() - t0) * 1000)

    answer = resp.get("answer", "")
    context = resp.get("context", [])

    meta = {
        "gating_mode": resp.get("gating_mode"),
        "gating_hint": resp.get("gating_hint", ""),
        "gating_metadata": resp.get("gating_metadata", {}),
        "used_model": resp.get("used_model"),
        "used_hyde": resp.get("used_hyde"),
        "used_rerank": resp.get("used_rerank", False),
        "top_k": resp.get("top_k"),
    }

    # Run-Item speichern
    upsert_run_item(
        pool=get_pool(),
        run_id=run_id,
        query_pk=qr["id"],
        answer_text=answer,
        citations=context,
        latency_ms=latency,
        meta=meta,
    )

    # Retrieval-Log mit Source (rrf vs ce)
    for i, chunk in enumerate(context):
        chunk_id = chunk.get("chunk_id")
        source = chunk.get("source", "rrf")  # rrf oder ce (cross-encoder)
        score = chunk.get("rerank_score") or chunk.get("rrf_score", 0.0)

        if chunk_id:
            upsert_retrieval_log(
                run_id=run_id,
                query_pk=qr["id"],
                chunk_id=chunk_id,
                rank=i + 1,
                score=float(score),
                source=source,
            )

    logger.debug(f"Query {qr['query_id']}: {latency}ms, {len(context)} chunks")


async def _run_all(
    rows: list[QueryRow], cfg: RunConfig, run_id: int, max_concurrency: int = 1
) -> None:
    client = QAClient(cfg.qa_base_url)
    sem = asyncio.Semaphore(max_concurrency)

    async def bounded(qr: QueryRow):
        async with sem:
            await _call_one(qr, client, cfg, run_id)

    await asyncio.gather(*[bounded(qr) for qr in rows])


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
            select id, query_id, text, process_name, process_id, roles, current_node_id, definition_id
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
                definition_id=r[7],
            )
            for r in cur.fetchall()
        ]

    if not rows:
        typer.echo(f"No queries for dataset='{cfg.dataset}'")
        raise typer.Exit(1)

    typer.echo(f"Executing {len(rows)} queries...")
    asyncio.run(_run_all(rows, cfg, run_id))
    typer.echo("Done.")


@app.command()
def score(
    run_name: str,
    reload_gold: bool = typer.Option(
        False,
        "--reload-gold",
        help="Gold-Daten aus Dateien neu laden (sonst nur aus DB)",
    ),
):
    """
    Compute per-query metrics and aggregate them.

    Flows:
    - Erstmalig: load-dataset + load-answers, dann score
    - Wiederholt: Nur score (nutzt DB-Daten)
    - Aktualisierung: score --reload-gold
    """
    pool = get_pool()

    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            "select id, config_json from ragrun.eval_runs where name=%s",
            (run_name,),
        )
        row = cur.fetchone()
        if not row:
            typer.echo(f"Run '{run_name}' not found.")
            raise typer.Exit(1)
        run_id, cfg_json = row
        cfg = RunConfig(**cfg_json)

    # Query-ID Mapping
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            "select id, query_id from ragrun.queries where dataset_name=%s",
            (cfg.dataset,),
        )
        qid_to_pk = {r[1]: r[0] for r in cur.fetchall()}

    # ================================================================
    # GOLD-DATEN: Version-aware Loading
    # ================================================================
    qrels_path = Path(cfg.get_qrels_path())
    answers_path = Path(cfg.get_answers_path())
    
    # Bestimme qrels_version aus Chunking-Strategie
    qrels_version = cfg.get_chunking_config().get_qrels_suffix()
    logger.info(f"Qrels-Version für diesen Run: {qrels_version}")

    # Prüfen ob Gold-Daten für DIESE VERSION bereits in DB existieren
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) FROM ragrun.gold_evidence ge
            JOIN ragrun.queries q ON ge.query_pk = q.id
            WHERE q.dataset_name = %s AND ge.qrels_version = %s
            """,
            (cfg.dataset, qrels_version),
        )
        qrels_exist = cur.fetchone()[0] > 0

        cur.execute(
            """
            SELECT COUNT(*) FROM ragrun.gold_answers ga
            JOIN ragrun.queries q ON ga.query_pk = q.id
            WHERE q.dataset_name = %s
            """,
            (cfg.dataset,),
        )
        answers_exist = cur.fetchone()[0] > 0

    if reload_gold or not qrels_exist:
        if qrels_path.exists():
            logger.info(f"Lade Qrels aus {qrels_path} (Version: {qrels_version})...")
            load_qrels(cfg.dataset, qid_to_pk, str(qrels_path), qrels_version=qrels_version)
        elif not qrels_exist:
            logger.warning(f"Qrels nicht gefunden: {qrels_path}")
    else:
        logger.info(
            f"Qrels (Version: {qrels_version}) bereits in DB, überspringe Laden"
        )

    if reload_gold or not answers_exist:
        if answers_path.exists():
            logger.info(f"Lade Answers aus {answers_path}...")
            for qid, answers, explanation in load_answers_jsonl(str(answers_path)):
                pk = qid_to_pk.get(qid)
                if pk:
                    upsert_gold_answers(pk, answers, explanation)
        elif not answers_exist:
            logger.warning(f"Answers nicht gefunden: {answers_path}")
    else:
        logger.info(
            "Answers bereits in DB, überspringe Laden (--reload-gold zum Neu-Laden)"
        )

    # ================================================================
    # GOLD-DATEN AUS DB LADEN (nur für diese Version!)
    # ================================================================
    gold_map: Dict[int, Dict[str, int]] = {}
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT ge.query_pk, ge.chunk_id, ge.relevance
            FROM ragrun.gold_evidence ge
            JOIN ragrun.queries q ON ge.query_pk = q.id
            WHERE q.dataset_name = %s AND ge.qrels_version = %s
            """,
            (cfg.dataset, qrels_version),
        )
        for qpk, cid, rel in cur.fetchall():
            gold_map.setdefault(qpk, {})[cid] = rel

    gold_answers_map: Dict[int, List[str]] = {}
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT ga.query_pk, ga.answers
            FROM ragrun.gold_answers ga
            JOIN ragrun.queries q ON ga.query_pk = q.id
            WHERE q.dataset_name = %s
            """,
            (cfg.dataset,),
        )
        for qpk, answers in cur.fetchall():
            if answers:
                gold_answers_map[qpk] = (
                    answers if isinstance(answers, list) else [answers]
                )

    # Run-Items laden
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            select ri.query_pk, ri.answer_text, ri.citations, q.id, q.query_id, q.text
            from ragrun.eval_run_items ri
            join ragrun.queries q on ri.query_pk = q.id
            where ri.run_id = %s
            """,
            (run_id,),
        )
        items = cur.fetchall()

    for query_pk, answer_text, citations, q_id, query_id, query_text in items:
        gold = gold_map.get(query_pk, {})
        gold_answers = gold_answers_map.get(query_pk, [])
        gold_chunk_ids = {k for k, v in gold.items() if v > 0}

        # Zitierte Chunk-IDs und Texte extrahieren
        cited_ids: List[str] = []
        cited_texts: List[str] = []
        if isinstance(citations, list):
            for c in citations:
                if isinstance(c, str):
                    cited_ids.append(c)
                elif isinstance(c, dict):
                    cid = c.get("chunk_id") or c.get("id") or c.get("chunkId")
                    if cid:
                        cited_ids.append(cid)
                    if c.get("text"):
                        cited_texts.append(c["text"])

        # Query-Metadaten laden
        with pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """select process_id, text, query_type 
                   from ragrun.queries where id=%s""",
                (query_pk,),
            )
            q_row = cur.fetchone()
            process_id = q_row[0] if q_row else None
            query_text = q_row[1] if q_row else ""
            query_type = q_row[2] if q_row and len(q_row) > 2 else "mixed"

        # Meta laden
        with pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """select meta from ragrun.eval_run_items 
                   where run_id=%s and query_pk=%s""",
                (run_id, query_pk),
            )
            row = cur.fetchone()
            meta = row[0] if row else {}

        gating_hint = meta.get("gating_hint", "")
        gating_metadata = meta.get("gating_metadata", {})

        # ============================================================
        # RETRIEVAL-METRIKEN (recall, ndcg, mrr)
        # ============================================================
        ranked: list[str] = []
        sources = list(cfg.ranking_sources or [])
        if sources:
            with pool.connection() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    select chunk_id
                    from ragrun.retrieval_logs
                    where run_id=%s and query_pk=%s and source = any(%s::text[])
                    order by array_position(%s::text[], source), rank asc
                    """,
                    (run_id, query_pk, sources, sources),
                )
                ranked = [r[0] for r in cur.fetchall()]

        if not ranked and cfg.ranking_fallback_all:
            with pool.connection() as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    select chunk_id from ragrun.retrieval_logs
                    where run_id=%s and query_pk=%s order by rank asc
                    """,
                    (run_id, query_pk),
                )
                ranked = [r[0] for r in cur.fetchall()]

        if ranked and gold:
            retrieval_metrics = compute_retrieval_metrics(ranked, gold, [3, 5, 10])
            for k, v in retrieval_metrics.items():
                upsert_score(run_id, query_pk, k, float(v))

        # ============================================================
        # GENERATION-METRIKEN (SemanticSim, ROUGE-L, Content-F1, BERTScore)
        # ============================================================
        if gold_answers and answer_text:
            best_gold = gold_answers[0]
            eval_cfg = cfg.get_evaluation_config()

            gen_metrics = compute_generation_metrics(
                answer_text,
                best_gold,
                semantic_sim_model=eval_cfg.semantic_sim_model,
                bertscore_model=eval_cfg.bertscore_model,
            )
            for k, v in gen_metrics.items():
                upsert_score(run_id, query_pk, k, float(v))

        # ============================================================
        # FAITHFULNESS-METRIKEN (CitationRecall, CitationPrecision, NLI)
        # ============================================================
        if answer_text:
            faith_metrics = compute_faithfulness_metrics(
                cited_chunk_ids=cited_ids,
                gold_chunk_ids=gold_chunk_ids,
            )
            for k, v in faith_metrics.items():
                upsert_score(run_id, query_pk, k, float(v))

        # ============================================================
        # LLM-JUDGE: REFERENCE-BASED (Factual Consistency)
        # ============================================================
        eval_cfg = cfg.factors.get("evaluation", {})
        use_llm_judge = eval_cfg.get("use_llm_judge", True)
        # Erweiterung: Granulare Kontrolle über Metriken
        judge_metrics = eval_cfg.get("llm_metrics", ["consistency"])
        judge_model = eval_cfg.get("judge_model", "atla/selene-mini")

        if use_llm_judge and answer_text:
            # 1. Factual Consistency (Reference Comparison)
            if gold_answers and "consistency" in judge_metrics:
                factual_results = judge_factual_consistency(
                    query=query_text,
                    response=answer_text,
                    gold_answer=gold_answers[0],
                    model=judge_model,
                )
                upsert_score(run_id, query_pk, "factual_consistency_score", float(factual_results["factual_consistency_score"]), details={"reasoning": factual_results.get("reasoning")})
                upsert_score(run_id, query_pk, "factual_consistency_normalized", float(factual_results["factual_consistency_normalized"]), details={"reasoning": factual_results.get("reasoning")})

            # 2. Answer Relevance (Query-Response Check)
            if "relevance" in judge_metrics:
                rel_results = judge_answer_relevance(
                    query=query_text,
                    response=answer_text,
                    model=judge_model
                )
                upsert_score(run_id, query_pk, "llm_answer_relevance", float(rel_results["answer_relevance_normalized"]), details={"reasoning": rel_results.get("reasoning")})

            # 3. Context Relevance (Query-Context Check)
            if "relevance" in judge_metrics and cited_texts:
                 ctx_results = judge_context_relevance(
                     query=query_text,
                     chunks=cited_texts,
                     model=judge_model
                 )
                 upsert_score(run_id, query_pk, "llm_context_relevance", float(ctx_results["context_relevance_normalized"]), details={"reasoning": ctx_results.get("reasoning")})

            # 4. Faithfulness (Response-Context Check)
            if "faithfulness" in judge_metrics and cited_texts:
                faith_results = judge_faithfulness(
                    response=answer_text,
                    chunks=cited_texts,
                    model=judge_model
                )
                upsert_score(run_id, query_pk, "llm_faithfulness", float(faith_results["faithfulness_normalized"]), details={"reasoning": faith_results.get("reasoning"), "hallucinated_statements": faith_results.get("hallucinated_statements")})

        # ============================================================
        # H2 GATING-METRIKEN
        # ============================================================
        gold_gating = get_gold_gating(query_pk)
        if gold_gating:
            # Meta und Query-Daten holen
            with pool.connection() as conn, conn.cursor() as cur:
                cur.execute(
                    """select meta from ragrun.eval_run_items 
                       where run_id=%s and query_pk=%s""",
                    (run_id, query_pk),
                )
                row = cur.fetchone()
                meta = row[0] if row else {}

            with pool.connection() as conn, conn.cursor() as cur:
                cur.execute(
                    """select process_id, text, query_type 
                       from ragrun.queries where id=%s""",
                    (query_pk,),
                )
                q_row = cur.fetchone()
                process_id = q_row[0] if q_row else None
                query_text = q_row[1] if q_row else ""
                query_type = q_row[2] if q_row and len(q_row) > 2 else "mixed"

            gating_hint = meta.get("gating_hint", "")
            gating_metadata = meta.get("gating_metadata", {})

            # ============================================================
            # 1. INPUT-METRIKEN (Manipulation Check) - Regelbasiert
            # ============================================================
            # Prüft: Wurde das Gating korrekt angewendet?
            # - Bei NONE: Sollte kein Gating-Kontext vorhanden sein
            # - Bei GATING_ENABLED: Sollte die erwarteten Lanes/Nodes enthalten

            predicted_gating = _extract_predicted_gating(gating_metadata)

            # Recall: Wurden die erwarteten Elemente im Gating verwendet?
            recall_metrics = gating_recall(predicted_gating, gold_gating)
            for metric_key, value in recall_metrics.items():
                upsert_score(run_id, query_pk, f"gating_{metric_key}", float(value))

            # Precision: Wurden nur erwartete Elemente verwendet?
            precision_metrics = gating_precision(predicted_gating, gold_gating)
            for metric_key, value in precision_metrics.items():
                upsert_score(run_id, query_pk, f"gating_{metric_key}", float(value))

            # ============================================================
            # 2. OUTPUT-METRIKEN (Effekt-Messung) - LLM-Judge (Selene)
            # ============================================================
            # Prüft: Hat das Gating die Antwortqualität verbessert?
            # - Weniger Scope-Violations?
            # - Weniger Halluzinationen?
            # - Bessere Rollengrenzen-Einhaltung?

            # Retrieved Chunks für Wissens-Fragen
            retrieved_chunks = []
            if isinstance(citations, list):
                for c in citations:
                    if isinstance(c, dict):
                        retrieved_chunks.append(c.get("text", ""))
                    elif isinstance(c, str):
                        retrieved_chunks.append(c)

            # Evaluation-Config
            eval_cfg = cfg.factors.get("evaluation", {})
            use_llm_judge = eval_cfg.get("use_llm_judge", True)
            judge_model = eval_cfg.get("judge_model", "atla/selene-mini")

            if use_llm_judge and answer_text:
                from .metrics.llm_judge import h2_judge_by_query_type

                h2_metrics = h2_judge_by_query_type(
                    query=query_text,
                    query_type=query_type,
                    response=answer_text,
                    gating_hint=gating_hint,
                    retrieved_chunks=retrieved_chunks,
                    expected_gating=gold_gating,
                    process_id=process_id,
                    model=judge_model,
                )

                for metric_name, value in h2_metrics.items():
                    if isinstance(value, (int, float)):
                        upsert_score(run_id, query_pk, metric_name, float(value))

    # Basis-Metriken (immer berechnen/reporten)
    default_metrics = {
             # Retrieval
            "recall@3", "recall@5", "recall@10",
            "mrr@3", "mrr@5", "mrr@10",
            "ndcg@3", "ndcg@5", "ndcg@10",
            # Generation
            "semantic_sim", "rouge_l_recall", "content_f1", "bertscore_f1",
            # Faithfulness
            "citation_recall", "citation_precision",
            # LLM-Judge (Legacy/Always)
            "factual_consistency_score", "factual_consistency_normalized",
            # H2 Gating
            "gating_lane_ids_recall", "gating_avg_gating_recall", "gating_avg_gating_precision",
            "h2_error_rate", "h2_structure_violation_rate", "h2_hallucination_rate",
            "h2_hint_adherence", "h2_knowledge_score", "h2_context_respected",
            "h2_integration_score", "h2_scope_violation_rate", "llm_judge_used",
    }
    
    # Metriken aus der Config hinzufügen (Primary/Secondary)
    cfg_metrics = set()
    if cfg and cfg.metrics:
        # Pydantic model vs dict access check
        m = cfg.metrics if isinstance(cfg.metrics, dict) else cfg.metrics.model_dump()
        cfg_metrics.update(m.get("primary", []))
        cfg_metrics.update(m.get("secondary", []))
        # Auch custom groups falls vorhanden
        if "ragas" in m:
             cfg_metrics.update(m["ragas"])

    final_metrics = list(default_metrics.union(cfg_metrics))

    report_path = aggregate_and_store(
        run_id,
        metrics=final_metrics,
    )
    typer.echo(f"Scores computed. Report written to {report_path}")


@app.command()
def study(study_config: str, execute: bool = True, fractional: bool = False):
    """Run a plan of OFAT variants or a factorial spec."""
    raw = yaml.safe_load(open(study_config, "r", encoding="utf-8").read())
    baseline_path = raw.get("baseline", "configs/baseline.yaml")
    baseline_cfg = RunConfig(
        **yaml.safe_load(open(baseline_path, "r", encoding="utf-8").read())
    )

    variants = raw.get("variants", [])
    variant_names: List[str] = []  # Sammle alle Variant-Namen
    
    # Track current model for unloading between runs
    current_model = _get_model_from_config(baseline_cfg)

    for var in variants:
        name = var.get("name", "UNNAMED")
        override = var.get("override", {})

        cfg = baseline_cfg.model_copy(deep=True)
        cfg.run_name = name

        if "qa_payload" in override:
            cfg.qa_payload.update(override["qa_payload"])
        if "factors" in override:
            for kk, vv in override["factors"].items():
                if isinstance(cfg.factors.get(kk), dict) and isinstance(vv, dict):
                    cfg.factors[kk].update(vv)
                else:
                    cfg.factors[kk] = vv

        temp_cfg_path = Path(f"configs/_temp_{name}.yaml")
        temp_cfg_path.write_text(
            yaml.dump(cfg.model_dump(), default_flow_style=False, allow_unicode=True)
        )

        typer.echo(f"\n=== Variant: {cfg.run_name} ===")
        if execute:
            # Check if model changed - unload ALL models to free VRAM
            new_model = _get_model_from_config(cfg)
            if new_model != current_model:
                typer.echo(f"Model changed: {current_model} → {new_model}")
                typer.echo("Unloading all models from VRAM...")
                _unload_all_ollama_models()
                current_model = new_model
            
            run(str(temp_cfg_path))
            score(cfg.run_name)
            variant_names.append(cfg.run_name)

        temp_cfg_path.unlink(missing_ok=True)

    if execute and variant_names:
        from .reporting import generate_study_report

        study_name = raw.get("name", Path(study_config).stem)
        primary_metrics = raw.get("metrics", {}).get(
            "primary",
            ["recall@5", "factual_consistency_normalized", "semantic_sim"],
        )
        secondary_metrics = raw.get("metrics", {}).get(
            "secondary",
            ["recall@3", "recall@10", "citation_recall"],
        )

        try:
            report_path = generate_study_report(
                study_name=study_name,
                baseline_run_name=baseline_cfg.run_name,
                variant_run_names=variant_names,
                primary_metrics=primary_metrics,
                secondary_metrics=secondary_metrics,
            )
            typer.echo(f"\n📊 Study Report: {report_path}")
        except Exception as e:
            typer.echo(f"⚠️ Study Report Fehler: {e}")


@app.command()
def compare(run_a: str, run_b: str, metric: str = "recall@5", iters: int = 2000):
    """Paired bootstrap comparison."""
    from .stats import paired_bootstrap

    pool = get_pool()

    def get_scores(run_name: str) -> Dict[int, float]:
        with pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                select s.query_pk, s.value
                from ragrun.scores s
                join ragrun.eval_runs r on s.run_id = r.id
                where r.name = %s and s.metric = %s
                """,
                (run_name, metric),
            )
            return {r[0]: r[1] for r in cur.fetchall()}

    scores_a = get_scores(run_a)
    scores_b = get_scores(run_b)

    common = set(scores_a.keys()) & set(scores_b.keys())
    if not common:
        typer.echo("No common queries found.")
        raise typer.Exit(1)

    a_vals = [scores_a[k] for k in sorted(common)]
    b_vals = [scores_b[k] for k in sorted(common)]

    result = paired_bootstrap(a_vals, b_vals, iters)
    typer.echo(f"Metric: {metric}")
    typer.echo(f"Run A ({run_a}): mean={result['mean_a']:.4f}")
    typer.echo(f"Run B ({run_b}): mean={result['mean_b']:.4f}")
    typer.echo(f"Diff (A-B): {result['mean_diff']:.4f}")
    typer.echo(f"95% CI: [{result['ci_lower']:.4f}, {result['ci_upper']:.4f}]")
    typer.echo(f"p-value: {result['p_value']:.4f}")


class QueryRow(TypedDict):
    id: int
    query_id: str
    text: str
    process_name: str | None
    process_id: str | None
    roles: list[str] | None
    current_node_id: str | None
    definition_id: str | None


@app.command()
def report(
    run_name: str,
    baseline: Optional[str] = None,
    out_dir: str = "reports",
):
    """Generate detailed report for a run, optionally comparing to baseline."""
    pool = get_pool()

    # Run-ID ermitteln
    with pool.connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT id FROM ragrun.eval_runs WHERE run_name = %s", (run_name,))
        row = cur.fetchone()
        if not row:
            typer.echo(f"Run '{run_name}' nicht gefunden.")
            raise typer.Exit(1)
        run_id = row[0]

        baseline_id = None
        if baseline:
            cur.execute(
                "SELECT id FROM ragrun.eval_runs WHERE run_name = %s", (baseline,)
            )
            row = cur.fetchone()
            if row:
                baseline_id = row[0]

    from .reporting import aggregate_and_store

    # Alle Metriken
    all_metrics = []
    for group in METRIC_GROUPS.values():
        all_metrics.extend(group["metrics"])

    report_path = aggregate_and_store(
        run_id=run_id,
        metrics=all_metrics,
        out_dir=out_dir,
        baseline_run_id=baseline_id,
    )

    typer.echo(f"📊 Report: {report_path}")


if __name__ == "__main__":
    setup_logging()
    app()
