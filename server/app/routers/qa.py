import logging
from fastapi import APIRouter

from app.core.models.askModel import AskBody
from app.core.prompt_builder import build_prompt
from app.services.retrieval import hybrid_search
from app.services.llm import ollama_generate
from app.services.gating import compute_gating, GatingMode

router = APIRouter(prefix="/api/qa")


@router.post("/ask")
def ask(body: AskBody):
    """
    Process-Aware QA Endpoint.

    Modi (automatisch bestimmt):
    - NONE: Kein current_node_id → Baseline (process_name nur als Retrieval-Filter)
    - PROCESS_CONTEXT: force_process_context=True → Grober Prozessüberblick (nur Ablation)
    - GATING_ENABLED: current_node_id gesetzt → Lokaler Prozesskontext
    """
    logging.info(
        "QA /ask: query=%s, process=%s, node=%s, roles=%s, force_ctx=%s",
        body.query[:50] if body.query else "",
        body.process_name,
        body.current_node_id,
        body.roles,
        body.force_process_context,
    )

    # 1) Gating berechnen
    gating = compute_gating(
        process_name=body.process_name,
        process_id=body.process_id,
        definition_id=body.definition_id,
        current_node_id=body.current_node_id,
        roles=body.roles or [],
        force_process_context=body.force_process_context,
    )

    logging.info(
        "Gating mode: %s, context_type: %s",
        gating.mode.value,
        gating.metadata.get("context_type"),
    )

    # 2) Retrieval mit process_name als Filter/Boost
    ctx = hybrid_search(
        body.query,
        body.top_k,
        process_name=body.process_name,
        tags=body.tags or None,
    )

    logging.info("Retrieved %d chunks", len(ctx))

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

    logging.debug("Prompt hint length: %d", len(gating.prompt_hint))

    # 5) LLM-Generierung
    answer = ollama_generate(prompt, model=body.model)

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
