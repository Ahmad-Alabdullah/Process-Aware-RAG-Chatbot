import time as time_module
from fastapi import APIRouter

from app.core.models.askModel import AskBody
from app.core.prompt_builder import build_prompt
from app.services.retrieval import hybrid_search
from app.services.llm import ollama_generate
from app.services.gating import compute_gating, GatingMode
from app.core.clients import get_logger

router = APIRouter(prefix="/api/qa")

logger = get_logger(__name__)


@router.post("/ask")
def ask(body: AskBody):
    """
    Process-Aware QA Endpoint.

    Modi (automatisch bestimmt):
    - NONE: Kein current_node_id → Baseline (process_name nur als Retrieval-Filter)
    - PROCESS_CONTEXT: force_process_context=True → Grober Prozessüberblick (nur Ablation)
    - GATING_ENABLED: current_node_id gesetzt → Lokaler Prozesskontext
    """
    logger.info(
        "QA /ask: query=%s, process=%s, node=%s, roles=%s, rerank=%s",
        body.query[:50] if body.query else "",
        body.process_name,
        body.current_node_id,
        body.roles,
        body.use_rerank,
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
    logger.info("Prompt building took %.3f seconds", t3 - t2)
    logger.info("📝 Prompt length: %d chars, ~%d tokens", len(prompt), len(prompt) // 4)

    # logger.debug("Prompt hint length: %d", len(gating.prompt_hint))

    # 5) LLM-Generierung
    answer = ollama_generate(prompt, model=body.model)

    t4 = time_module.perf_counter()
    logger.info("LLM generation took %.3f seconds", t4 - t3)
    logger.info("⏱️ Total: %.2fs", t4 - t0)
    logger.info("📤 Answer length: %d chars, ~%d tokens", len(answer), len(answer) // 4)

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
        "top_k": body.top_k,
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
