from fastapi import APIRouter, Query
from app.services.retrieval import hybrid_search
from app.core.config import settings
from app.core.clients import get_opensearch

router = APIRouter(prefix="/api/search")


@router.get("/search")
def search(q: str = Query(...), top_k: int = Query(default=5)):
    results = hybrid_search(q, top_k)
    return {"q": q, "results": results}


@router.get("/process-names")
def get_process_names(os_index: str = Query("chunks_semantic_qwen3")):
    """
    Returns distinct process_names from OpenSearch documents.
    Used for the process selector dropdown.
    """
    os_client = get_opensearch()
    
    # Aggregation query to get unique process_names
    agg_query = {
        "size": 0,
        "aggs": {
            "process_names": {
                "terms": {
                    "field": "meta.process_name",
                    "size": 100
                }
            }
        }
    }
    
    try:
        response = os_client.search(index=os_index, body=agg_query)
        buckets = response.get("aggregations", {}).get("process_names", {}).get("buckets", [])
        
        process_names = [
            {
                "name": bucket["key"],
                "doc_count": bucket["doc_count"],
                "has_model": False  # Will be merged with BPMN data on frontend
            }
            for bucket in buckets
            if bucket["key"]  # Filter out empty strings
        ]
        
        return {"ok": True, "process_names": process_names}
    except Exception as e:
        return {"ok": False, "error": str(e), "process_names": []}
