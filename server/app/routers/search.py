from fastapi import APIRouter, Query
from app.services.retrieval import hybrid_search
from app.core.config import settings

router = APIRouter()


@router.get("/search")
def search(q: str = Query(...), top_k: int = Query(default=5)):
    results = hybrid_search(q, top_k)
    return {"q": q, "results": results}
