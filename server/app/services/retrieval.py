from typing import List, Dict, Any, Optional, Set

from app.core.config import settings
from app.core.clients import get_logger, get_opensearch, get_qdrant
from app.services.pipeline import embed_texts

logger = get_logger(__name__)


def rrf(rank: int, k: Optional[int] = None) -> float:
    k = k or settings.RRF_K
    return 1.0 / (k + rank)


def _terms(field: str, values):
    """Hilfsfunktion: immer als Liste an `terms` übergeben, auf `.keyword` ausweichen."""
    if values is None:
        return None
    if not isinstance(values, (list, tuple, set)):
        values = [values]
    values = [v for v in values if v is not None and v != ""]
    if not values:
        return None
    # exakte Filter über `.keyword`
    return {"terms": {f"{field}.keyword": list(values)}}


def embed_texts_dynamic(
    texts: List[str],
    backend: str = "hf",
    model: str = "sentence-transformers/all-minilm-l6-v2",
) -> List[List[float]]:
    """
    Embedding mit dynamischer Backend/Modell-Auswahl.

    Args:
        texts: Texte zum Embedden
        backend: "ollama" oder "hf"
        model: Modellname

    Returns:
        Liste von Embedding-Vektoren
    """
    if backend == "hf":
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(model)
        return _model.encode(texts, normalize_embeddings=True).tolist()
    else:
        import requests

        resp = requests.post(
            f"{settings.OLLAMA_BASE}/api/embed",
            json={"model": model, "input": texts},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["embeddings"]


def hybrid_search(
    q: str,
    k: int,
    *,
    # optionale Filter
    process_name: Optional[str] = None,
    tags: Optional[List[str]] = None,
    use_rerank: bool = False,
    rerank_top_n: int = 50,
    os_index: Optional[str] = None,
    qdrant_collection: Optional[str] = None,
    embedding_backend: str = "hf",
    embedding_model: str = "sentence-transformers/all-minilm-l6-v2",
) -> List[Dict[str, Any]]:
    """
    Hybrid Search mit dynamischer Embedding-Konfiguration.

    Args:
        q: Query
        k: Anzahl der Ergebnisse
        process_name: Filter nach Prozessname
        tags: Filter nach Tags
        use_rerank: Reranking aktivieren
        rerank_top_n: Anzahl Kandidaten für Reranking
        os_index: OpenSearch Index (default aus settings)
        qdrant_collection: Qdrant Collection (default aus settings)
        embedding_backend: "ollama" oder "hf"
        embedding_model: Modellname für Embeddings

    Returns:
        Liste von Chunks mit Scores
    """

    os_client = get_opensearch()
    qd = get_qdrant()

    # Index-Namen
    os_idx = os_index or settings.OS_INDEX
    qd_col = qdrant_collection or settings.QDRANT_COLLECTION

    # Wenn Reranking aktiv, mehr Kandidaten holen
    fetch_k = rerank_top_n if use_rerank else k * 5

    # ---------- 1) OpenSearch: Volltext + Filter ----------
    should = [
        {
            "multi_match": {
                "query": q,
                "fields": [
                    "text^3",
                    "meta.process_name^5",
                    "meta.tags^2",
                ],
                "type": "best_fields",
            }
        }
    ]

    os_filters: List[Dict[str, Any]] = []

    t = _terms("meta.process_name", process_name)
    if t:
        os_filters.append(t)

    t = _terms("meta.tags", tags)
    if t:
        os_filters.append(t)

    bool_query: Dict[str, Any] = {"should": should}
    if os_filters:
        bool_query["filter"] = os_filters

    os_resp = os_client.search(
        index=os_idx,
        body={
            "size": fetch_k,
            "query": {"bool": bool_query},
        },
    )

    os_hits = os_resp["hits"]["hits"]
    os_rrf = {h["_id"]: rrf(i) for i, h in enumerate(os_hits, start=1)}

    # ---------- 2) Qdrant: Vektor + Payload-Filter ----------
    from qdrant_client.http.models import Filter, FieldCondition, MatchValue, MatchAny

    must_conditions = []

    if process_name:
        must_conditions.append(
            FieldCondition(key="process_name", match=MatchValue(value=process_name))
        )
    if tags:
        if isinstance(tags, str):
            tags_list = [tags]
        else:
            tags_list = list(tags)

        must_conditions.append(
            FieldCondition(
                key="tags",
                match=MatchAny(any=tags_list),
            )
        )

    qfilter = Filter(must=must_conditions) if must_conditions else None

    # Dynamisches Embedding
    vec = embed_texts_dynamic([q], backend=embedding_backend, model=embedding_model)[0]

    qd_hits = qd.search(
        collection_name=qd_col,
        query_vector=vec,
        limit=fetch_k,
        query_filter=qfilter,
        with_payload=True,
    )

    qd_rrf: Dict[str, float] = {}
    for i, p in enumerate(qd_hits, start=1):
        cid = (p.payload or {}).get("chunk_id") or str(p.id)
        qd_rrf[cid] = rrf(i)

    # ---------- 3) Fusion ----------
    fused = os_rrf.copy()
    for cid, s in qd_rrf.items():
        fused[cid] = fused.get(cid, 0.0) + s

    candidate_k = rerank_top_n if use_rerank else k
    top_ids = [
        cid
        for cid, _ in sorted(fused.items(), key=lambda x: x[1], reverse=True)[
            :candidate_k
        ]
    ]

    # ---------- 4) Quellen nachladen ----------
    results: List[Dict[str, Any]] = []
    if top_ids:
        mget = os_client.mget(index=os_idx, body={"ids": top_ids})
        id_to_doc = {}
        for d in mget["docs"]:
            if d.get("found"):
                src = d["_source"]
                meta = src.get("meta", {})
                id_to_doc[d["_id"]] = {
                    "chunk_id": d["_id"],
                    "text": src.get("text", ""),
                    "document_id": src.get("document_id"),
                    "process_name": meta.get("process_name"),
                    "tags": meta.get("tags"),
                    "page_number": meta.get("page_number"),
                    "section_title": meta.get("section_title"),
                    "rrf_score": fused.get(d["_id"], 0.0),
                    "source": "rrf",
                }

        for cid in top_ids:
            if cid in id_to_doc:
                results.append(id_to_doc[cid])

    # ---------- 5) Optionales Reranking ----------
    if use_rerank and results:
        from app.services.reranking import rerank, unload_reranker

        logger.info(f"Reranking {len(results)} candidates → top {k}")
        results = rerank(q, results, top_k=k, text_key="text")
        # logger.info(f"Reranking done: {results}")
        
        # GPU-Speicher freigeben für Ollama LLM
        # unload_reranker()
    else:
        # fusion onlyy
        results = results[:k]

    # Rank-Feld hinzufügen
    for i, doc in enumerate(results):
        doc["rank"] = i + 1

    return results
