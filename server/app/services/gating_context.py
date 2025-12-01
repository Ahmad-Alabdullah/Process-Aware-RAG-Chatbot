"""
Berechnet den Gating-Kontext für PROCESS-Queries.
Kann sowohl zur Laufzeit als auch vorab für Evaluation genutzt werden.
"""

from typing import Any, Dict, List, Optional
from app.core.clients import get_logger
from app.services.bpmn_store import lane_and_task_labels, local_process_view
from app.services.whitelist import allowed_for_principal

logger = get_logger(__name__)


def compute_gating_context(
    process_id: Optional[str] = None,
    definition_id: Optional[str] = None,
    roles: Optional[List[str]] = None,
    current_node_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Berechnet den Gating-Kontext für eine Query.

    Args:
        process_id: BPMN Process-ID (z.B. "Process_Dienstreise")
        definition_id: BPMN Definition-ID für Whitelist-Lookup
        roles: Liste der Nutzerrollen
        current_node_id: Aktueller Knoten im Prozess (optional)

    Returns:
        Dict mit lane_ids, node_ids, lane_names, task_names, local_view
    """
    context: Dict[str, Any] = {
        "lane_ids": [],
        "node_ids": [],
        "lane_names": [],
        "task_names": [],
        "local_view": None,
    }

    if not roles:
        roles = []

    # Whitelist-basierte Lanes/Nodes ermitteln
    if definition_id and roles:
        try:
            agg = allowed_for_principal(definition_id=definition_id, roles=roles)
            context["lane_ids"] = list(agg.get("laneIds", []))
            context["node_ids"] = list(agg.get("nodeIds", []))
            logger.debug(
                f"Whitelist für {roles}: {len(context['lane_ids'])} Lanes, "
                f"{len(context['node_ids'])} Nodes"
            )
        except Exception as e:
            logger.warning(f"Whitelist-Lookup fehlgeschlagen: {e}")

    # Labels für Lanes und Tasks holen
    if process_id and (context["lane_ids"] or context["node_ids"]):
        try:
            labels = lane_and_task_labels(
                process_id=process_id,
                lane_ids=context["lane_ids"],
                node_ids=context["node_ids"],
            )
            context["lane_names"] = [
                l.get("name") for l in labels.get("lanes", []) if l.get("name")
            ]
            context["task_names"] = [
                t.get("name") for t in labels.get("tasks", []) if t.get("name")
            ]
            logger.debug(
                f"Labels: {context['lane_names']}, Tasks: {context['task_names'][:5]}..."
            )
        except Exception as e:
            logger.warning(f"Lane/Task-Labels fehlgeschlagen: {e}")

    # Lokale Prozessansicht (Vorgänger/Nachfolger)
    if process_id and current_node_id:
        try:
            local = local_process_view(
                process_id=process_id,
                current_node_id=current_node_id,
                max_depth=2,
            )
            if local:
                context["local_view"] = dict(local)
                logger.debug(
                    f"Local view: current={local.get('current', {}).get('name')}"
                )
        except Exception as e:
            logger.warning(f"Local process view fehlgeschlagen: {e}")

    return context


def build_gating_hint_from_context(
    context: Dict[str, Any],
    process_name: Optional[str] = None,
    roles: Optional[List[str]] = None,
) -> str:
    """
    Baut den Gating Hint aus dem vorab berechneten Kontext.

    Args:
        context: Output von compute_gating_context()
        process_name: Name des Prozesses für Kontext-Satz
        roles: Nutzerrollen für Kontext-Satz

    Returns:
        Gating Hint als String für den Prompt
    """
    parts: List[str] = []

    if process_name:
        parts.append(
            f"Du beantwortest die Frage im Kontext des Prozesses '{process_name}'."
        )

    if roles:
        roles_str = ", ".join(roles)
        parts.append(f"Die Nutzerrolle(n): {roles_str}.")

    lane_names = context.get("lane_names", [])
    task_names = context.get("task_names", [])

    if lane_names:
        lanes_str = ", ".join(lane_names)
        parts.append(
            f"Antworte nur zu Schritten, die folgenden Lanes zugeordnet sind: {lanes_str}."
        )

    if task_names:
        # Maximal 10 Tasks anzeigen, um Prompt nicht zu überladen
        display_tasks = task_names[:10]
        tasks_str = ", ".join(display_tasks)
        suffix = (
            f" (und {len(task_names) - 10} weitere)" if len(task_names) > 10 else ""
        )
        parts.append(
            f"Konzentriere dich insbesondere auf folgende Aufgaben: {tasks_str}{suffix}."
        )

    local_view = context.get("local_view")
    if local_view and local_view.get("current"):
        cur = local_view["current"]
        cur_name = cur.get("name") or cur.get("id")
        cur_lane = cur.get("laneName")

        preds = [
            n.get("name") or n.get("id")
            for n in (local_view.get("predecessors") or [])[:3]
            if n.get("name") or n.get("id")
        ]
        succs = [
            n.get("name") or n.get("id")
            for n in (local_view.get("successors") or [])[:3]
            if n.get("name") or n.get("id")
        ]

        sentence = f"Der Nutzer befindet sich aktuell bei Schritt '{cur_name}'"
        if cur_lane:
            sentence += f" (Lane: {cur_lane})"
        sentence += ". "

        if preds:
            sentence += f"Vorhergehende Schritte: {', '.join(preds)}. "
        if succs:
            sentence += f"Mögliche nächste Schritte: {', '.join(succs)}."

        parts.append(sentence)

    return "\n".join(parts) if parts else ""


def get_definition_id_for_process(process_name: str) -> Optional[str]:
    """
    Ermittelt die Definition-ID für einen Prozessnamen.
    Fallback: Sucht in Neo4j nach passendem Process.
    """
    from app.core.clients import get_neo4j

    try:
        driver = get_neo4j()
        with driver.session() as s:
            result = s.run(
                """
                MATCH (d:BPMN)-[:CONTAINS]->(p:Process)
                WHERE p.name = $pname OR d.name CONTAINS $pname
                RETURN d.definitionId AS defId
                LIMIT 1
                """,
                pname=process_name,
            ).single()

            if result:
                return result["defId"]
    except Exception as e:
        logger.warning(f"Definition-ID Lookup fehlgeschlagen: {e}")

    return None
