from typing import List, Dict, Any, Optional, Set
from app.core.config import settings
from app.core.clients import get_opensearch, get_qdrant
from app.services.pipeline import embed_texts
from app.services.whitelist import (
    allowed_for_principal,
    allowed_nodes_union,
    build_os_filter,
    build_qdrant_filter,
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
    whitelist: bool = False,
    process_id: Optional[str] = None,
    principal_id: Optional[str] = None,
    whitelist_ids: Optional[List[str]] = None,
    definition_id: Optional[str] = None,
    roles: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    os_client = get_opensearch()
    qd = get_qdrant()

    # --- 0) Whitelist-Auswertung (optional) ---
    allow_node_ids: Set[str] = set()
    allow_lane_ids: Set[str] = set()

    if whitelist:
        if whitelist_ids:  # explizit
            rows = allowed_nodes_union(process_id, whitelist_ids)
            for r in rows:
                if r.get("nodeId"):
                    allow_node_ids.add(r["nodeId"])
                if r.get("laneId"):
                    allow_lane_ids.add(r["laneId"])
        elif definition_id and (principal_id or roles):
            # BPMN-Upload erzeugt Lane-Whitelist-Regeln;
            rows = allowed_for_principal(definition_id, principal_id, roles or [])
            for r in rows:
                if r.get("nodeId"):
                    allow_node_ids.add(r["nodeId"])
                if r.get("laneId"):
                    allow_lane_ids.add(r["laneId"])

    # --- 1) BM25 (OpenSearch) ---
    should = [{"match": {"text": q}}]
    if role:
        should.append({"match": {"meta.roles": role}})
    if section:
        should.append({"match": {"meta.section_title": section}})

    # Filter aus Whitelist zusammenbauen (processId/nodeId/laneId)
    os_filter = build_os_filter(
        process_id=process_id,
        node_ids=list(allow_node_ids) or None,
        lane_ids=list(allow_lane_ids) or None,
    )

    os_resp = os_client.search(
        index=settings.OS_INDEX,
        body={
            "size": k * 5,
            "query": {"bool": {"should": should, "filter": os_filter or []}},
        },
    )
    os_hits = os_resp["hits"]["hits"]
    os_rrf = {h["_id"]: rrf(i) for i, h in enumerate(os_hits, start=1)}

    # --- 2) Vector (Qdrant) ---
    from qdrant_client.http.models import Filter

    qd_filter: Optional[Filter] = build_qdrant_filter(
        process_id=process_id,
        node_ids=list(allow_node_ids) or None,
        lane_ids=list(allow_lane_ids) or None,
    )

    vec = embed_texts([q])[0]
    qd_hits = qd.search(
        collection_name=settings.QDRANT_COLLECTION,
        query_vector=vec,
        limit=k * 5,
        query_filter=qd_filter,
        with_payload=True,
    )

    qd_rrf = {}
    for i, p in enumerate(qd_hits, start=1):
        cid = (p.payload or {}).get("chunk_id") or str(p.id)
        qd_rrf[cid] = rrf(i)

    # --- 3) RRF + 4) mget ---
    fused = os_rrf.copy()
    for cid, s in qd_rrf.items():
        fused[cid] = fused.get(cid, 0.0) + s

    top_ids = [
        cid for cid, _ in sorted(fused.items(), key=lambda x: x[1], reverse=True)[:k]
    ]
    mget = os_client.mget(index=settings.OS_INDEX, body={"ids": top_ids})
    docs_by_id = {d["_id"]: d["_source"] for d in mget["docs"] if d.get("found")}
    return [
        {"chunk_id": cid, "score": fused[cid], **docs_by_id.get(cid, {})}
        for cid in top_ids
        if docs_by_id.get(cid)
    ]
