"""
Pre-Flight Check für Evaluation Runs.

Prüft alle Voraussetzungen vor dem Start.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.core.clients import get_opensearch, get_qdrant, get_neo4j, get_logger
from app.core.config import settings
from app.eval.db import get_pool

logger = get_logger(__name__)


def check_databases():
    """Prüft Datenbankverbindungen."""
    errors = []

    # PostgreSQL
    try:
        pool = get_pool()
        with pool.connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
        logger.info("✅ PostgreSQL: OK")
    except Exception as e:
        errors.append(f"❌ PostgreSQL: {e}")

    # OpenSearch
    try:
        os_client = get_opensearch()
        info = os_client.info()
        logger.info(f"✅ OpenSearch: {info['version']['number']}")
    except Exception as e:
        errors.append(f"❌ OpenSearch: {e}")

    # Qdrant
    try:
        qd = get_qdrant()
        collections = qd.get_collections()
        logger.info(f"✅ Qdrant: {len(collections.collections)} collections")
    except Exception as e:
        errors.append(f"❌ Qdrant: {e}")

    # Neo4j
    try:
        driver = get_neo4j()
        with driver.session() as s:
            s.run("RETURN 1")
        logger.info("✅ Neo4j: OK")
    except Exception as e:
        errors.append(f"❌ Neo4j: {e}")

    return errors


def check_indices(index_name: str = "chunks"):
    """Prüft ob Indices existieren und Daten enthalten."""
    errors = []

    # OpenSearch Index
    try:
        os_client = get_opensearch()
        if os_client.indices.exists(index=index_name):
            count = os_client.count(index=index_name)["count"]
            logger.info(f"✅ OpenSearch Index '{index_name}': {count} docs")
        else:
            errors.append(f"❌ OpenSearch Index '{index_name}' existiert nicht")
    except Exception as e:
        errors.append(f"❌ OpenSearch Index: {e}")

    # Qdrant Collection
    try:
        qd = get_qdrant()
        cols = [c.name for c in qd.get_collections().collections]
        if index_name in cols:
            info = qd.get_collection(index_name)
            logger.info(
                f"✅ Qdrant Collection '{index_name}': {info.points_count} points"
            )
        else:
            errors.append(f"❌ Qdrant Collection '{index_name}' existiert nicht")
    except Exception as e:
        errors.append(f"❌ Qdrant Collection: {e}")

    return errors


def check_datasets(dataset_name: str = "demo"):
    """Prüft ob Dataset-Dateien existieren."""
    errors = []
    base = Path("datasets")

    required_files = [
        f"{dataset_name}_queries.jsonl",
        f"{dataset_name}_answers.jsonl",
    ]

    optional_files = [
        f"{dataset_name}_qrels.jsonl",
        f"{dataset_name}_qrels_1800.jsonl",  # Alternative
    ]

    for f in required_files:
        path = base / f
        if path.exists():
            lines = sum(1 for _ in open(path, "r", encoding="utf-8"))
            logger.info(f"✅ {f}: {lines} Zeilen")
        else:
            errors.append(f"❌ {f} fehlt")

    # Mindestens eine Qrels-Datei
    qrels_found = False
    for f in optional_files:
        path = base / f
        if path.exists():
            lines = sum(1 for _ in open(path, "r", encoding="utf-8"))
            logger.info(f"✅ {f}: {lines} Zeilen")
            qrels_found = True
            break

    if not qrels_found:
        errors.append(f"❌ Keine Qrels-Datei gefunden für {dataset_name}")

    return errors


def check_ollama_models():
    """Prüft ob benötigte Ollama-Modelle verfügbar sind."""
    import requests

    errors = []

    required_models = [
        "qwen3:8b",  # QA-Generierung
        "atla/selene-mini",  # LLM-Judge
    ]

    optional_models = [
        "EmbeddingGemma:300m",  # Semantic Similarity
        "qwen3-embedding:4b",  # Alternative Embeddings
    ]

    try:
        resp = requests.get(f"{settings.OLLAMA_BASE}/api/tags", timeout=10)
        resp.raise_for_status()
        available = {m["name"] for m in resp.json().get("models", [])}

        for model in required_models:
            if model in available or any(model in m for m in available):
                logger.info(f"✅ Ollama Model '{model}': verfügbar")
            else:
                errors.append(f"❌ Ollama Model '{model}' fehlt (ollama pull {model})")

        for model in optional_models:
            if model in available or any(model in m for m in available):
                logger.info(f"✅ Ollama Model '{model}': verfügbar (optional)")
            else:
                logger.warning(f"⚠️ Ollama Model '{model}' fehlt (optional)")

    except Exception as e:
        errors.append(f"❌ Ollama nicht erreichbar: {e}")

    return errors


def check_db_schema():
    """Prüft ob alle Tabellen existieren."""
    errors = []

    required_tables = [
        "ragrun.eval_runs",
        "ragrun.queries",
        "ragrun.gold_evidence",
        "ragrun.gold_answers",
        "ragrun.gold_gating",
        "ragrun.eval_run_items",
        "ragrun.eval_scores",
        "ragrun.retrieval_logs",
        "ragrun.aggregates",
    ]

    try:
        pool = get_pool()
        with pool.connection() as conn, conn.cursor() as cur:
            for table in required_tables:
                schema, name = table.split(".")
                cur.execute(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = %s AND table_name = %s
                    )
                    """,
                    (schema, name),
                )
                exists = cur.fetchone()[0]
                if exists:
                    logger.info(f"✅ Tabelle {table}: OK")
                else:
                    errors.append(f"❌ Tabelle {table} fehlt")
    except Exception as e:
        errors.append(f"❌ Schema-Check: {e}")

    return errors


def main():
    """Führt alle Pre-Flight Checks durch."""
    from app.core.clients import setup_logging

    setup_logging(level="INFO")

    print("\n" + "=" * 60)
    print("PRE-FLIGHT CHECK: RAG Evaluation")
    print("=" * 60 + "\n")

    all_errors = []

    print("1. Datenbanken...")
    all_errors.extend(check_databases())

    print("\n2. DB-Schema...")
    all_errors.extend(check_db_schema())

    print("\n3. Indices...")
    all_errors.extend(check_indices("chunks"))

    print("\n4. Datasets...")
    all_errors.extend(check_datasets("demo"))

    print("\n5. Ollama Models...")
    all_errors.extend(check_ollama_models())

    print("\n" + "=" * 60)
    if all_errors:
        print(f"❌ {len(all_errors)} FEHLER GEFUNDEN:")
        for e in all_errors:
            print(f"   {e}")
        print("\nBitte beheben vor Start der Evaluation!")
        return 1
    else:
        print("✅ ALLE CHECKS BESTANDEN - Evaluation kann starten!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
