from typing import List, Optional
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from app.services.retrieval import hybrid_search
from app.services.llm import ollama_generate, hyde_rewrite
from app.core.config import settings

router = APIRouter(prefix="/api/qa")


class AskBody(BaseModel):
    # Query + Retrieval
    query: str
    top_k: int = int(settings.TOP_K)

    # HYDE + LLM
    use_hyde: bool = False
    model: str = settings.OLLAMA_MODEL

    # Kontext-Filter
    process_name: Optional[str] = None
    tags: Optional[List[str]] = None
    roles: List[str] = Field(default_factory=list, description="Rollen des Principals")

    # Whitelist-Gating
    whitelist_enabled: bool = Field(
        False, description="Ob Whitelist-Gating aktiviert ist"
    )
    lane_ids: Optional[List[str]] = None
    node_ids: Optional[List[str]] = None


@router.post("/ask")
def ask(body: AskBody, request: Request):
    q = hyde_rewrite(body.query, model=body.model) if body.use_hyde else body.query
    ctx = hybrid_search(
        q,
        body.top_k,
        roles=body.roles or None,
        process_name=body.process_name or None,
        tags=body.tags or None,
        whitelist_enabled=body.whitelist_enabled,
        lane_ids=body.lane_ids or None,
        node_ids=body.node_ids or None,
    )
    context_text = "\n\n".join(f"- {c['text']}" for c in ctx)
    gating_hint = (
        "\n(Nutze nur Informationen aus freigegebenen Prozessbereichen.)\n"
        if body.whitelist_enabled
        else ""
    )
    prompt = f"""Beantworte die Frage basierend auf dem Kontext.{gating_hint}

                 Frage: {body.query}

                 Kontext:{context_text}

                 Antwort (deutsch, mit kurzen Belegen wenn möglich):

              """
    answer = ollama_generate(prompt, model=body.model)
    return {
        "answer": answer,
        "context": ctx,
        "whitelist": body.whitelist_enabled,
        "used_model": body.model,
        "used_hyde": body.use_hyde,
        "top_k": body.top_k,
    }


class RetrieveIn(BaseModel):
    query: str
    k: int = Field(int(settings.TOP_K), ge=1, le=50)
    role: Optional[str] = None
    section: Optional[str] = None
    whitelist: bool = False
    process_id: Optional[str] = None
    principal_id: Optional[str] = None
    whitelist_ids: List[str] = Field(default_factory=list)


class RetrieveOut(BaseModel):
    ok: bool
    count: int
    principal_id: Optional[str]
    results: List[dict]


# no-llm-retrieval
@router.post(
    "/retrieve",
    response_model=RetrieveOut,
    summary="No-LLM Hybrid Retrieval (BM25+Vector) mit optionalem Whitelist-Gating",
)
def retrieve(body: RetrieveIn, request: Request):
    principal_from_header = request.headers.get("X-Principal-Id")
    principal_id = body.principal_id or principal_from_header

    results = hybrid_search(
        body.query,
        body.k,
        role=body.role,
        section=body.section,
        whitelist=body.whitelist,
        process_id=body.process_id,
        principal_id=principal_id,
        whitelist_ids=body.whitelist_ids or None,
    )
    return RetrieveOut(
        ok=True, count=len(results), principal_id=principal_id, results=results
    )
