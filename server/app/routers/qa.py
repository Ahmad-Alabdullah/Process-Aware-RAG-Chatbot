import time as time_module
from fastapi import APIRouter, Query
from transformers import Optional

from app.core.models.askModel import AskBody
from app.core.prompt_builder import build_prompt
from app.services.retrieval import hybrid_search
from app.services.llm import ollama_generate
from app.services.gating import compute_gating, GatingMode
from app.core.clients import get_logger
from app.core.config import settings
from app.core.llm_config import LLMPresets

router = APIRouter(prefix="/api/qa")

logger = get_logger(__name__)


@router.post("/ask")
def ask(
    body: AskBody,
    # Optionale Overrides für Evaluation
    os_index: Optional[str] = Query(None, description="OpenSearch Index Override"),
    qdrant_collection: Optional[str] = Query(
        None, description="Qdrant Collection Override"
    ),
    embedding_backend: Optional[str] = Query(None, description="'ollama' oder 'hf'"),
    embedding_model: Optional[str] = Query(None, description="Embedding Modellname"),
    # LLM-Parameter (optional für Experimente)
    temperature: Optional[float] = Query(
        None, ge=0.0, le=2.0, description="Temperature Override (default: 0.1 für QA)"
    ),
):
    """
    Process-Aware QA Endpoint.

    Modi (automatisch bestimmt):
    - NONE: Kein current_node_id → Baseline (process_name nur als Retrieval-Filter)
    - PROCESS_CONTEXT: force_process_context=True → Grober Prozessüberblick (nur Ablation)
    - GATING_ENABLED: current_node_id gesetzt → Lokaler Prozesskontext

    Temperature-Defaults (wissenschaftlich fundiert):
    - QA-Generierung: 0.1 (niedriges T für Faktentreue)
    - HyDE: 0.3 (höheres T für Variabilität)
    - CoT: 0.2 (moderates T für Reasoning)
    """
    logger.info(
        "QA /ask: query=%s, process=%s, node=%s, rerank=%s, emb=%s/%s",
        body.query[:50] if body.query else "",
        body.process_name,
        body.current_node_id,
        body.use_rerank,
        embedding_backend or "default",
        embedding_model or "default",
        temperature or "default",
    )

    t0 = time_module.perf_counter()

    # 1) Gating berechnen
    gating = compute_gating(
        process_name=body.process_name,
        process_id=body.process_id,
        definition_id=body.definition_id,
        current_node_id=body.current_node_id,
        roles=body.roles or [],
        force_process_context=body.force_process_context,
    )

    t1 = time_module.perf_counter()
    logger.info("Gating computation took %.3f seconds", t1 - t0)

    # logger.info(
    #     "Gating mode: %s, context_type: %s",
    #     gating.mode.value,
    #     gating.metadata.get("context_type"),
    # )

    # 2) Retrieval mit optionalem Reranking
    ctx = hybrid_search(
        body.query,
        body.top_k,
        process_name=body.process_name,
        tags=body.tags or None,
        use_rerank=body.use_rerank,
        rerank_top_n=body.rerank_top_n,
        # Dynamische Config
        os_index=os_index,
        qdrant_collection=qdrant_collection,
        embedding_backend=embedding_backend or settings.EMBEDDING_BACKEND,
        embedding_model=embedding_model or settings.EMBEDDING_MODEL,
    )

    t2 = time_module.perf_counter()
    logger.info(
        "Retrieval took %.3f seconds (rerank=%s, candidates=%d)",
        t2 - t1,
        body.use_rerank,
        body.rerank_top_n if body.use_rerank else body.top_k * 5,
    )

    # logger.info("Retrieved %d chunks", len(ctx))

    # 3) Kontext aufbereiten
    context_text = "\n\n".join(
        [
            f"[{i+1}] (Quelle: {c.get('chunk_id', 'unbekannt')})\n{c.get('text', '')}"
            for i, c in enumerate(ctx)
        ]
    )

    # 4) Prompt bauen
    prompt = build_prompt(
        style=body.prompt_style,
        body=body,
        context_text=context_text,
        gating_hint=gating.prompt_hint,
    )

    t3 = time_module.perf_counter()

    # 6) LLM-Generierung mit passender Config
    if body.prompt_style == "cot":
        llm_config = LLMPresets.chain_of_thought(model=body.model)
    else:
        llm_config = LLMPresets.rag_qa(model=body.model)

    # Temperature Override falls angegeben
    if temperature is not None:
        llm_config.temperature = temperature

    answer = ollama_generate(prompt, config=llm_config)

    t4 = time_module.perf_counter()
    logger.info(
        "⏱️ Total: %.2fs (gating=%.2f, retrieval=%.2f, prompt=%.2f, llm=%.2f)",
        t4 - t0,
        t1 - t0,
        t2 - t1,
        t3 - t2,
        t4 - t3,
    )

    # 6) Response
    response = {
        "answer": answer,
        "context": ctx,
        "gating_mode": gating.mode.value,
        "gating_hint": gating.prompt_hint,
        "gating_metadata": gating.metadata,
        "whitelist": gating.mode == GatingMode.GATING_ENABLED,
        "used_model": body.model,
        "used_hyde": body.use_hyde,
        "used_rerank": body.use_rerank,
        "used_temperature": llm_config.temperature,
        "top_k": body.top_k,
        "embedding_config": {
            "backend": embedding_backend or settings.EMBEDDING_BACKEND,
            "model": embedding_model or settings.EMBEDDING_MODEL,
        },
    }

    # Position-Details für GATING_ENABLED
    if gating.position and gating.position.current:
        response["position"] = {
            "current_node": gating.position.current.display_name(),
            "current_node_id": gating.position.current.id,
            "current_lane": gating.position.current.lane_name,
            "allowed_successors": [
                {
                    "name": s.display_name(),
                    "is_gateway": s.is_gateway,
                    "branches": (
                        [b.describe() for b in s.branches] if s.is_gateway else []
                    ),
                }
                for s in gating.position.successors
            ],
        }

    # Overview für PROCESS_CONTEXT (Ablation)
    if gating.overview:
        response["process_overview"] = {
            "all_lanes": gating.overview.all_lanes,
            "all_steps": gating.overview.all_steps[:10],
            "key_decisions": gating.overview.key_decisions,
        }

    return response
