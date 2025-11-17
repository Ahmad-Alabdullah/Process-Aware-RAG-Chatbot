import logging
from typing import List, Optional
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from app.services.retrieval import hybrid_search
from app.services.llm import ollama_generate, hyde_rewrite
from app.core.config import settings
from app.services.bpmn_store import lane_and_task_labels
from app.services.whitelist import allowed_for_principal

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
    definition_id: Optional[str] = None
    process_id: Optional[str] = None


@router.post("/ask")
def ask(body: AskBody, request: Request):
    q = hyde_rewrite(body.query, model=body.model) if body.use_hyde else body.query
    ctx = hybrid_search(
        q,
        body.top_k,
        process_name=body.process_name or None,
        tags=body.tags or None,
    )
    context_text = "\n\n".join(f"- {c['text']}" for c in ctx)

    gating_hint = ""
    if body.whitelist_enabled and body.definition_id:
        # Welche Nodes/Lanes sind erlaubt?
        agg = allowed_for_principal(
            definition_id=body.definition_id,
            roles=body.roles or [],
        )
        lane_ids = agg["laneIds"]
        node_ids = agg["nodeIds"]

        logging.warning(
            f"Whitelist gating enabled. Allowed lane_ids: {lane_ids}, node_ids: {node_ids}"
        )

        labels = lane_and_task_labels(
            process_id=body.process_id or "",
            lane_ids=lane_ids,
            node_ids=node_ids,
        )

        logging.warning(f"Whitelist gating labels: {labels}")

        lane_names = [l["name"] or l["id"] for l in labels["lanes"]]
        task_names = [t["name"] or t["id"] for t in labels["tasks"]]

        logging.warning(
            f"Whitelist gating lane_names: {lane_names}, task_names: {task_names}"
        )

        gating_hint = f"""
        Du beantwortest die Frage im Kontext des Prozesses '{body.process_name}'.
        Die Nutzerrolle(n): {", ".join(body.roles or [])}.

        Antworte nur zu Schritten, die folgenden Lanes zugeordnet sind:
        {", ".join(lane_names) if lane_names else "(keine Lanes hinterlegt)"}.

        Konzentriere dich insbesondere auf folgende Aufgaben:
        {", ".join(task_names) if task_names else "(keine konkreten Aufgaben hinterlegt)"}.

        Für alle anderen Prozessschritte darfst du höchstens grob beschreiben,
        dass andere Rollen zuständig sind (z. B. Dekan, Finanzabteilung), ohne deren
        interne Details oder Entscheidungskriterien zu erläutern.
        """

        logging.warning(f"Gating hint: {gating_hint}")

    prompt = f"""Beantworte die Frage basierend auf dem Kontext.{gating_hint}

                 Frage: {body.query}

                 Kontext:{context_text}

                 Antwort (deutsch, mit kurzen Belegen und Zitate aus dem Kontext, wenn möglich):

              """

    answer = ollama_generate(prompt, model=body.model)
    return {
        "answer": answer,
        "context": ctx,
        "gating_hint": gating_hint,
        "whitelist": body.whitelist_enabled,
        "used_model": body.model,
        "used_hyde": body.use_hyde,
        "top_k": body.top_k,
    }
