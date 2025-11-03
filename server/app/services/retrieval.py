from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.clients import get_opensearch, get_qdrant
from app.services.pipeline import embed_texts
from server.app.services.whitelist import (
    allowed_nodes_union,
    build_os_filter,
    build_qdrant_filter,
    whitelists_for_principal,
)


def rrf(rank: int, k: Optional[int] = None) -> float:
    k = k or settings.RRF_K
    return 1.0 / (k + rank)


def hybrid_search(
    q: str,
    k: int,
    *,
    role: Optional[str] = None,
    section: Optional[str] = None,
    # NEW: Whitelist-Gating
    whitelist: bool = False,
    process_id: Optional[str] = None,
    principal_id: Optional[str] = None,
    whitelist_ids: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    os_client = get_opensearch()
    qd = get_qdrant()

    # -------- Whitelist-Auflösung --------
    wids = list(whitelist_ids or [])
    if principal_id:
        wids.extend(whitelists_for_principal(principal_id))
    wids = list(dict.fromkeys(wids))  # de-dupe

    allow_node_ids = set()
    if whitelist and process_id and wids:
        # union der erlaubten Node-IDs über alle Whitelists des Principals
        allow_node_ids, _ = allowed_nodes_union(wids, process_id)

    # -------- 1) BM25 (OpenSearch) mit Boosts via bool.should --------
    # Quelle: OpenSearch bool query (must/should/filter)
    should = [{"match": {"text": q}}]
    if role:
        should.append({"match": {"meta.roles": role}})
    if section:
        should.append({"match": {"meta.section_title": section}})

    # Wenn Gating aktiv ist: Filter hart erzwingen
    if whitelist and process_id:
        os_filter = build_os_filter(
            process_id,
            node_ids=list(allow_node_ids) if allow_node_ids else None,
        )
        os_query = {"bool": {"should": should, **os_filter["bool"]}}
    else:
        os_query = {"bool": {"should": should}}

    os_resp = os_client.search(
        index=settings.OS_INDEX,
        body={"size": k * 5, "query": os_query},
    )
    os_hits = os_resp["hits"]["hits"]
    os_rrf = {h["_id"]: rrf(i) for i, h in enumerate(os_hits, start=1)}

    # -------- 2) Vector (Qdrant) + optionaler Payload-Filter auf Rolle --------
    from qdrant_client.http.models import Filter, FieldCondition, MatchValue

    qfilter = None
    if role and not (whitelist and process_id):
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue

        qfilter = Filter(
            must=[FieldCondition(key="roles", match=MatchValue(value=role))]
        )

    if whitelist and process_id:
        qfilter = build_qdrant_filter(
            process_id,
            node_ids=list(allow_node_ids) if allow_node_ids else None,
        )

    vec = embed_texts([q])[0]
    qd_hits = qd.search(
        collection_name=settings.QDRANT_COLLECTION,
        query_vector=vec,
        limit=k * 5,
        query_filter=qfilter,
        with_payload=True,
    )

    # über gemeinsame chunk_id fusionieren
    qd_rrf: Dict[str, float] = {}
    for i, p in enumerate(qd_hits, start=1):
        cid = (p.payload or {}).get("chunk_id") or str(p.id)
        qd_rrf[cid] = rrf(i)

    # -------- 3) RRF-Fusion (OS + Qdrant) --------
    fused = os_rrf.copy()
    for cid, s in qd_rrf.items():
        fused[cid] = fused.get(cid, 0.0) + s

    top_ids = [
        cid for cid, _ in sorted(fused.items(), key=lambda x: x[1], reverse=True)[:k]
    ]

    # -------- 4) Quellen --------
    # OpenSearch Multi-Get API
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
        score = fused.get(cid, 0.0)
        results.append({"chunk_id": cid, "score": score, **src})
    return results
