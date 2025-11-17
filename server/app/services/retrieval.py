import logging
from typing import List, Dict, Any, Optional, Set
from app.core.config import settings
from app.core.clients import get_opensearch, get_qdrant
from app.services.pipeline import embed_texts


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


def hybrid_search(
    q: str,
    k: int,
    *,
    # optionale Filter
    process_name: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    os_client = get_opensearch()
    qd = get_qdrant()

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

    logging.warning(f"OpenSearch hybrid_search bool_query: {bool_query}")

    os_resp = os_client.search(
        index=settings.OS_INDEX,
        body={
            "size": k * 5,
            "query": {"bool": bool_query},
        },
    )

    logging.warning(
        f"OpenSearch hybrid_search found {os_resp['hits']['total']['value']} hits"
    )

    os_hits = os_resp["hits"]["hits"]
    os_rrf = {h["_id"]: rrf(i) for i, h in enumerate(os_hits, start=1)}

    # ---------- 2) Qdrant: Vektor + Payload-Filter ----------
    from qdrant_client.http.models import Filter, FieldCondition, MatchValue

    must_conditions = []
    if process_name:
        must_conditions.append(
            FieldCondition(key="process_name", match=MatchValue(value=process_name))
        )
    if tags:
        must_conditions.append(
            FieldCondition(
                key="tags",
                match=MatchValue(
                    value=tags[0] if isinstance(tags, list) and len(tags) == 1 else tags
                ),
            )
        )

    qfilter = Filter(must=must_conditions) if must_conditions else None

    vec = embed_texts([q])[0]
    qd_hits = qd.search(
        collection_name=settings.QDRANT_COLLECTION,
        query_vector=vec,
        limit=k * 5,
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

    top_ids = [
        cid for cid, _ in sorted(fused.items(), key=lambda x: x[1], reverse=True)[:k]
    ]

    logging.warning(f"Fused top_ids: {top_ids}")

    # ---------- 4) Quellen nachladen ----------
    if top_ids:
        mget = os_client.mget(index=settings.OS_INDEX, body={"ids": top_ids})
        docs_by_id = {d["_id"]: d["_source"] for d in mget["docs"] if d.get("found")}

    results: List[Dict[str, Any]] = []
    for cid in top_ids:
        src = docs_by_id.get(cid)
        if not src:
            try:
                src = os_client.get(index=settings.OS_INDEX, id=cid)["_source"]
            except Exception:
                continue
        results.append({"chunk_id": cid, "score": fused.get(cid, 0.0), **src})
    return results
