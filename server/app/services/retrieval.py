from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.clients import get_opensearch, get_qdrant
from app.services.pipeline import embed_texts


def rrf(rank: int, k: Optional[int] = None) -> float:
    k = k or settings.RRF_K
    return 1.0 / (k + rank)


def hybrid_search(
    q: str, k: int, *, role: Optional[str] = None, section: Optional[str] = None
) -> List[Dict[str, Any]]:
    os_client = get_opensearch()
    qd = get_qdrant()

    # -------- 1) BM25 (OpenSearch) mit Boosts via bool.should --------
    # Quelle: OpenSearch bool query (must/should/filter)
    should = [{"match": {"text": q}}]
    if role:
        should.append({"match": {"meta.roles": role}})
    if section:
        should.append({"match": {"meta.section_title": section}})

    # Größerer Kandidatenpuffer für RRF
    os_resp = os_client.search(
        index=settings.OS_INDEX,
        body={"size": k * 5, "query": {"bool": {"should": should}}},
    )
    os_hits = os_resp["hits"]["hits"]
    os_rrf = {h["_id"]: rrf(i) for i, h in enumerate(os_hits, start=1)}

    # -------- 2) Vector (Qdrant) + optionaler Payload-Filter auf Rolle --------
    # Qdrant Payload-Filter (roles == role) – siehe Doku/Beispiele
    from qdrant_client.http.models import Filter, FieldCondition, MatchValue

    qfilter = None
    if role:
        qfilter = Filter(
            must=[FieldCondition(key="roles", match=MatchValue(value=role))]
        )

    vec = embed_texts([q])[0]
    qd_hits = qd.search(
        collection_name=settings.QDRANT_COLLECTION,
        query_vector=vec,
        limit=k * 5,
        query_filter=qfilter,
        with_payload=True,
    )

    # WICHTIG: über gemeinsame chunk_id fusionieren (liegt im Qdrant-Payload)
    # (Sorge dafür, dass du beim Indexieren payload["chunk_id"] = f"{doc_id}:{i}" schreibst.)
    qd_rrf: Dict[str, float] = {}
    for i, p in enumerate(qd_hits, start=1):
        cid = (p.payload or {}).get("chunk_id") or str(p.id)
        qd_rrf[cid] = rrf(i)

    # -------- 3) RRF-Fusion (OS + Qdrant) --------
    # RRF ist der empfohlene Fuser für Hybrid-Suche (Azure/OpenSearch)
    fused = os_rrf.copy()
    for cid, s in qd_rrf.items():
        fused[cid] = fused.get(cid, 0.0) + s

    top_ids = [
        cid for cid, _ in sorted(fused.items(), key=lambda x: x[1], reverse=True)[:k]
    ]

    # -------- 4) Quellen per mget ziehen (performant) --------
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
