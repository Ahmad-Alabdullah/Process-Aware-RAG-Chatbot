import logging
from typing import List, Literal, Optional
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from app.services.retrieval import hybrid_search
from app.services.llm import ollama_generate, hyde_rewrite
from app.services.bpmn_store import lane_and_task_labels, local_process_view
from app.services.whitelist import allowed_for_principal
from app.core.prompt_builder import build_prompt
from app.core.models.askModel import AskBody

router = APIRouter(prefix="/api/qa")


@router.post("/ask")
def ask(body: AskBody):
    logging.info("QA /ask called with body=%s", body.model_dump())

    # 1) HYDE-Rewrite
    q = body.query
    # if body.use_hyde:
    #     try:
    #         q = hyde_rewrite(body.query, model=body.model)
    #         logging.info(
    #             "HYDE rewrite successful. Original='%s', hyde='%s'", body.query, q
    #         )
    #     except Exception as e:
    #         logging.exception("HYDE rewrite failed, fallback to original query: %s", e)
    #         q = body.query

    # 2) Whitelist-Gating (Lane/Node-IDs)
    lane_ids: List[str] = list(body.lane_ids or [])
    node_ids: List[str] = list(body.node_ids or [])

    local_view = None

    if body.whitelist_enabled:
        # Falls UI lane_ids/node_ids NICHT explizit mitgibt, aus Whitelist ableiten
        if body.definition_id and body.roles:
            try:
                agg = allowed_for_principal(
                    definition_id=body.definition_id,
                    roles=body.roles or [],
                )
                auto_lane_ids = list(agg.get("laneIds", []))
                auto_node_ids = list(agg.get("nodeIds", []))

                if not lane_ids:
                    lane_ids = auto_lane_ids
                if not node_ids:
                    node_ids = auto_node_ids

                logging.warning(
                    "Whitelist gating (auto) enabled. Roles=%s, lane_ids=%s, node_ids=%s",
                    body.roles,
                    lane_ids,
                    node_ids,
                )
            except Exception as e:
                logging.exception("allowed_for_principal failed: %s", e)

        # Lokaler BPMN-Kontext um aktuellen Knoten
        if body.process_id and body.current_node_id:
            try:
                local_view = local_process_view(
                    process_id=body.process_id,
                    current_node_id=body.current_node_id,
                    max_depth=2,
                )
                logging.warning("local_process_view: %s", local_view)
            except Exception as e:
                logging.exception("local_process_view failed: %s", e)
                local_view = None

    # 4) Retrieval mit allen Gating-Informationen
    ctx = hybrid_search(
        q,
        body.top_k,
        process_name=body.process_name or None,
        tags=body.tags or None,
    )

    logging.warning("Retrieval context size: %d", len(ctx))

    context_text = "\n\n".join(
        [
            f"[{i+1}] (Quelle: {c.get('meta', {}).get('source', 'unbekannt')})\n{c.get('text', '')}"
            for i, c in enumerate(ctx)
        ]
    )

    # 5) Gating-Hint zusammenbauen (Prozess + Rolle + Lane/Tasks + lokale Nachbarschaft)
    gating_hint = ""
    if body.whitelist_enabled:
        parts: List[str] = []

        if body.process_name:
            parts.append(
                f"Du beantwortest die Frage im Kontext des Prozesses '{body.process_name}', der in BPMN modelliert ist."
            )

        if body.roles:
            parts.append(f"Die Nutzerrolle(n): {', '.join(body.roles)}.")

        # Labels für Lanes/Tasks aus Neo4j
        lane_names: List[str] = []
        task_names: List[str] = []

        if body.process_id and (lane_ids or node_ids):
            labels = lane_and_task_labels(
                process_id=body.process_id,
                lane_ids=lane_ids or [],
                node_ids=node_ids or [],
            )
            lane_names = [l.get("name") or l.get("id") for l in labels.get("lanes", [])]
            task_names = [t.get("name") or t.get("id") for t in labels.get("tasks", [])]

            if lane_names:
                parts.append(
                    "Antworte nur zu Schritten, die folgenden Lanes zugeordnet sind: "
                    + ", ".join(lane_names)
                    + "."
                )

            if task_names:
                parts.append(
                    "Konzentriere dich insbesondere auf folgende Aufgaben: "
                    + ", ".join(task_names)
                    + "."
                )

        # Lokale Vorgänger/Nachfolger an der aktuellen Position
        if local_view and local_view.get("current"):
            cur = local_view["current"]
            cur_name = cur.get("name") or cur.get("id") or "aktueller Schritt"

            allowed_lanes = set(lane_ids or [])
            preds = local_view.get("predecessors", []) or []
            succs = local_view.get("successors", []) or []

            # bevorzugt Nodes in erlaubten Lanes, sonst fallback auf alle
            def _filter_nodes(nodes):
                if not nodes:
                    return []
                in_allowed = [
                    n
                    for n in nodes
                    if not allowed_lanes or n.get("laneId") in allowed_lanes
                ]
                return in_allowed or nodes

            preds_filtered = _filter_nodes(preds)[:3]
            succs_filtered = _filter_nodes(succs)[:3]

            preds_names = [n.get("name") or n.get("id") for n in preds_filtered]
            succs_names = [n.get("name") or n.get("id") for n in succs_filtered]

            sentence = f"Der Nutzer befindet sich aktuell bei '{cur_name}'. "
            if preds_names:
                sentence += (
                    "Typische vorhergehende Schritte in seinem Kontext sind: "
                    + ", ".join(preds_names)
                    + ". "
                )
            if succs_names:
                sentence += (
                    "Mögliche nächste Schritte von hier (im erlaubten Kontext) sind: "
                    + ", ".join(succs_names)
                    + ". "
                )
            sentence += "Formuliere deine Antwort so, dass sie zu dieser lokalen Prozessposition passt. Und verwende keine BPMN-spezifischen Begriffe wie 'Lane' oder 'Task', sondern beschreibe die Schritte neutral."

            parts.append(sentence)

        # Übergeordnete Restriktion für andere Lanes
        parts.append(
            "Für alle anderen Prozessschritte darfst du höchstens grob beschreiben, "
            "dass andere Rollen zuständig sind (z. B. Dekan, Finanzabteilung), "
            "ohne deren internen Ablauf oder Entscheidungskriterien im Detail zu erläutern."
        )

        gating_hint = "\n        ".join(parts)
        logging.warning("Gating hint:\n%s", gating_hint)

    # 6) Finales Prompt
    prompt = build_prompt(
        style=body.prompt_style,
        body=body,
        context_text=context_text,
        gating_hint=gating_hint,
    )

    answer = ollama_generate(prompt, model=body.model)

    return {
        "ok": True,
        "query": body.query,
        # "rewrite": q if body.use_hyde else None,
        "context": context_text,
        "answer": answer,
        "gating_hint": gating_hint,
        "prompt": prompt,
    }
