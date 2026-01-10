"""
Process-Aware Gating Service mit Gateway-Handling.

Zwei Modi im Normalbetrieb:
1. NONE: Baseline (kein current_node_id, auch wenn process_name vorhanden)
2. GATING_ENABLED: Lokaler, rollenspezifischer Kontext (current_node_id gesetzt)

PROCESS_CONTEXT wird nur in Ablation-Studies explizit aktiviert.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

from app.core.clients import get_logger
from app.services.bpmn_store import (
    local_process_view_with_gateways,
)
from app.services.whitelist import allowed_for_principal

logger = get_logger(__name__)


class GatingMode(str, Enum):
    NONE = "none"  # Baseline: Kein Prozesskontext im Prompt
    PROCESS_CONTEXT = "process"  # Ablation: Grober Prozessüberblick
    GATING_ENABLED = "gating"  # Lokal + Rollenspezifisch (Task ausgewählt)


@dataclass
class GatewayBranch:
    """Ein ausgehender Pfad von einem Gateway."""

    target_id: str
    target_name: str
    target_type: str
    condition: Optional[str] = None
    condition_name: Optional[str] = None
    description: Optional[str] = None

    def describe(self) -> str:
        """Menschenlesbare Beschreibung des Pfads."""
        if self.condition_name:
            return f"Falls '{self.condition_name}': → {self.target_name}"
        elif self.condition:
            return f"Wenn {self.condition}: → {self.target_name}"
        else:
            return f"→ {self.target_name}"


@dataclass
class NodeInfo:
    """Knoten-Information mit optionalen Gateway-Branches."""

    id: str
    name: str
    type: str
    description: Optional[str] = None
    lane_name: Optional[str] = None
    lane_id: Optional[str] = None
    is_gateway: bool = False
    branches: List[GatewayBranch] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: Dict) -> "NodeInfo":
        branches = []
        if d.get("is_gateway") and d.get("branches"):
            branches = [
                GatewayBranch(
                    target_id=b.get("id", ""),
                    target_name=b.get("name", ""),
                    target_type=b.get("type", ""),
                    condition=b.get("condition"),
                    condition_name=b.get("conditionName"),
                    description=b.get("description"),
                )
                for b in d["branches"]
            ]

        return cls(
            id=d.get("id", ""),
            name=d.get("name", ""),
            type=d.get("type", ""),
            description=d.get("description"),
            lane_name=d.get("laneName"),
            lane_id=d.get("laneId"),
            is_gateway=d.get("is_gateway", False),
            branches=branches,
        )

    def display_name(self) -> str:
        return self.name or self.id

    def describe_gateway(self) -> str:
        """Beschreibt Gateway mit allen Branches."""
        if not self.is_gateway:
            return self.display_name()

        gateway_type = self._gateway_type_name()
        branch_descs = [b.describe() for b in self.branches]

        if branch_descs:
            return f"{gateway_type} '{self.display_name()}': {'; '.join(branch_descs)}"
        return f"{gateway_type} '{self.display_name()}'"

    def _gateway_type_name(self) -> str:
        if self.type == "exclusiveGateway":
            return "Entscheidung"
        elif self.type == "parallelGateway":
            return "Parallele Ausführung"
        elif self.type == "inclusiveGateway":
            return "Optionale Verzweigung"
        return "Gateway"


@dataclass
class ProcessOverview:
    """Vollständiger Prozessüberblick (für Ablation PROCESS_CONTEXT)."""

    process_name: str
    lanes_with_tasks: List[Dict[str, Any]] = field(default_factory=list)
    nodes_without_lane: List[Dict[str, Any]] = field(default_factory=list)
    flows: List[Dict[str, Any]] = field(default_factory=list)
    gateways: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class LocalPosition:
    """Lokale Position mit Gateway-Awareness (GATING_ENABLED Modus)."""

    current: Optional[NodeInfo] = None
    predecessors: List[NodeInfo] = field(default_factory=list)
    successors: List[NodeInfo] = field(default_factory=list)
    allowed_lanes: List[str] = field(default_factory=list)
    allowed_nodes: List[str] = field(default_factory=list)


@dataclass
class GatingResult:
    """Ergebnis des Gating-Prozesses."""

    mode: GatingMode
    process_name: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    overview: Optional[ProcessOverview] = None
    position: Optional[LocalPosition] = None
    prompt_hint: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


def determine_mode(
    current_node_id: Optional[str],
    force_process_context: bool = False,
) -> GatingMode:
    """
    Bestimmt den Gating-Modus.

    Logik:
    - current_node_id gesetzt → GATING_ENABLED
    - force_process_context=True (nur Ablation) → PROCESS_CONTEXT
    - Sonst → NONE (Baseline)

    Hinweis: process_name wird NUR als Retrieval-Filter verwendet,
    nicht für die Modus-Entscheidung im Normalbetrieb.
    """
    if current_node_id:
        return GatingMode.GATING_ENABLED

    if force_process_context:
        return GatingMode.PROCESS_CONTEXT

    return GatingMode.NONE


def compute_gating(
    process_name: Optional[str] = None,
    process_id: Optional[str] = None,
    definition_id: Optional[str] = None,
    current_node_id: Optional[str] = None,
    roles: Optional[List[str]] = None,
    force_process_context: bool = False,  # Nur für Ablation-Study
) -> GatingResult:
    """
    Berechnet Gating mit Gateway-Awareness.

    Args:
        process_name: Name des Prozesses (für Retrieval-Filter, nicht Modus)
        process_id: BPMN Process-ID (xmlId)
        definition_id: BPMN Definition-ID für Whitelist
        current_node_id: Aktueller Knoten (aktiviert GATING_ENABLED)
        roles: Nutzerrollen für Whitelist-Filter
        force_process_context: Nur für Ablation - erzwingt PROCESS_CONTEXT Modus

    Returns:
        GatingResult mit Modus, Kontext und Prompt-Hint
    """
    roles = roles or []
    mode = determine_mode(current_node_id, force_process_context)

    result = GatingResult(
        mode=mode,
        process_name=process_name,
        roles=roles,
    )

    # === NONE: Baseline ===
    if mode == GatingMode.NONE:
        result.prompt_hint = ""
        result.metadata = {"context_type": "none"}
        return result

    # === PROCESS_CONTEXT: Grober Überblick (nur Ablation) ===
    if mode == GatingMode.PROCESS_CONTEXT:
        result.overview = _compute_process_overview_with_decisions(
            process_id, process_name
        )
        result.prompt_hint = _build_overview_hint(result)
        result.metadata = {
            "context_type": "overview",
            "num_lanes": len(result.overview.lanes_with_tasks) if result.overview else 0,
            "num_decisions": len(result.overview.gateways) if result.overview else 0,
            "num_steps": (
                sum(len(l.get("nodes", [])) for l in result.overview.lanes_with_tasks)
                + len(result.overview.nodes_without_lane)
            )
            if result.overview
            else 0,
        }
        return result

    # === GATING_ENABLED: Lokal + Rollenspezifisch ===
    result.position = _compute_local_position_with_gateways(
        process_id=process_id,
        definition_id=definition_id,
        current_node_id=current_node_id,
        roles=roles,
    )
    result.prompt_hint = _build_gating_hint_with_gateways(result)

    # Metadata
    gateway_count = (
        sum(1 for s in (result.position.successors or []) if s.is_gateway)
        if result.position
        else 0
    )

    result.metadata = {
        "context_type": "gating",
        "num_allowed_lanes": (
            len(result.position.allowed_lanes) if result.position else 0
        ),
        "num_allowed_nodes": (
            len(result.position.allowed_nodes) if result.position else 0
        ),
        "num_successors": len(result.position.successors) if result.position else 0,
        "num_gateways": gateway_count,
        "current_node": (
            result.position.current.display_name()
            if result.position and result.position.current
            else None
        ),
        "current_lane": (
            result.position.current.lane_name
            if result.position and result.position.current
            else None
        ),
    }

    return result


def _compute_process_overview_with_decisions(
    process_id: Optional[str],
    process_name: Optional[str],
) -> ProcessOverview:
    """
    Vollständiger Prozessüberblick MIT allen Beziehungen (für Ablation).

    Holt ALLE Informationen:
    - Alle Lanes mit allen zugeordneten Tasks
    - Alle Sequence Flows (Beziehungen)
    - Alle Gateways mit Branches
    """
    if not process_id:
        return ProcessOverview(process_name=process_name or "Unbekannt")

    try:
        from app.services.bpmn_store import get_process_overview_full

        overview_data = get_process_overview_full(process_id)

        if not overview_data:
            return ProcessOverview(process_name=process_name or "Unbekannt")

        return ProcessOverview(
            process_name=process_name or overview_data.get("name", "Unbekannt"),
            # Vollständige Daten
            lanes_with_tasks=overview_data.get("lanes", []),
            nodes_without_lane=overview_data.get("nodes_without_lane", []),
            flows=overview_data.get("flows", []),
            gateways=overview_data.get("gateways", []),
        )

    except Exception as e:
        logger.info(f"Process overview fehlgeschlagen: {e}")
        return ProcessOverview(process_name=process_name or "Unbekannt")


def _compute_local_position_with_gateways(
    process_id: Optional[str],
    definition_id: Optional[str],
    current_node_id: Optional[str],
    roles: List[str],
) -> LocalPosition:
    """Lokale Position mit Gateway-Branches (für GATING_ENABLED)."""
    position = LocalPosition()

    # 1. Whitelist: Erlaubte Lanes/Nodes für Rollen
    if definition_id and roles:
        try:
            agg = allowed_for_principal(definition_id=definition_id, roles=roles)
            position.allowed_lanes = list(agg.get("laneIds", []))
            position.allowed_nodes = list(agg.get("nodeIds", []))
            logger.debug(
                f"Whitelist: {len(position.allowed_lanes)} Lanes, "
                f"{len(position.allowed_nodes)} Nodes für {roles}"
            )
        except Exception as e:
            logger.info(f"Whitelist-Lookup fehlgeschlagen: {e}")

    # 2. Lokale Ansicht MIT Gateways
    if process_id and current_node_id:
        try:
            local = local_process_view_with_gateways(
                process_id=process_id,
                current_node_id=current_node_id,
                max_depth=2,
            )
            if local:
                if local.get("current"):
                    position.current = NodeInfo.from_dict(local["current"])

                # Vorgänger (Gateways filtern)
                position.predecessors = [
                    NodeInfo.from_dict(p)
                    for p in (local.get("predecessors") or [])[:3]
                    if "Gateway" not in p.get("type", "")
                ]

                # Nachfolger: MIT Gateways und deren Branches
                raw_successors = local.get("successors") or []

                # Bei Whitelist: Filtern auf erlaubte Lanes/Nodes
                if position.allowed_lanes or position.allowed_nodes:
                    filtered = []
                    for s in raw_successors:
                        if s.get("is_gateway"):
                            s_copy = dict(s)
                            if s.get("branches"):
                                s_copy["branches"] = [
                                    b
                                    for b in s["branches"]
                                    if b.get("id") in position.allowed_nodes
                                    or not position.allowed_nodes
                                ]
                            filtered.append(s_copy)
                        elif (
                            s.get("id") in position.allowed_nodes
                            or s.get("laneId") in position.allowed_lanes
                            or not position.allowed_nodes
                        ):
                            filtered.append(s)
                    raw_successors = filtered

                position.successors = [
                    NodeInfo.from_dict(s) for s in raw_successors[:5]
                ]

        except Exception as e:
            logger.info(f"Local process view fehlgeschlagen: {e}")

    return position


# ============ PROMPT HINTS ============


def _build_overview_hint(result: GatingResult) -> str:
    """
    PROCESS_CONTEXT: Vollständiger Prozesskontext mit allen Beziehungen.

    Zeigt:
    - Alle Lanes mit ihren Tasks (inkl. Typ-Hints)
    - Alle Beziehungen zwischen Tasks (Prozessfluss)
    - Alle Entscheidungspunkte mit Branches
    """
    if not result.overview:
        return f"Die Frage bezieht sich auf den Prozess '{result.process_name}'."

    parts: List[str] = []
    ov = result.overview

    # 1. Prozessname
    parts.append(f"## Prozess: {ov.process_name}")

    # 2. Lanes mit ihren Tasks (vollständig)
    if ov.lanes_with_tasks:
        parts.append("\n### Rollen und ihre Aufgaben:")
        for lane in ov.lanes_with_tasks:
            lane_name = lane.get("name") or "Unbenannte Rolle"
            nodes = lane.get("nodes", [])
            if nodes:
                task_strs = []
                for n in nodes:
                    name = n.get("name") or n.get("id")
                    type_hint = _get_type_hint(n.get("type", ""))
                    if type_hint:
                        task_strs.append(f"'{name}' ({type_hint})")
                    else:
                        task_strs.append(f"'{name}'")
                parts.append(f"- **{lane_name}**: {', '.join(task_strs)}")

    # 3. Prozessfluss (alle Beziehungen)
    if ov.flows:
        parts.append("\n### Prozessablauf:")
        # Gruppiere nach Startpunkt für bessere Lesbarkeit
        flow_strs = []
        for flow in ov.flows:
            from_name = flow.get("from", "?")
            to_name = flow.get("to", "?")
            condition = flow.get("condition")
            if condition:
                flow_strs.append(f"'{from_name}' → '{to_name}' (wenn: {condition})")
            else:
                flow_strs.append(f"'{from_name}' → '{to_name}'")
        parts.append("; ".join(flow_strs))

    # 4. Entscheidungspunkte (Gateways mit allen Branches)
    if ov.gateways:
        parts.append("\n### Entscheidungspunkte:")
        for gw in ov.gateways:
            gw_name = gw.get("name") or gw.get("id")
            gw_type = _get_gateway_type_name(gw.get("type", ""))
            branches = gw.get("branches", [])
            if branches:
                branch_strs = []
                for b in branches:
                    target = b.get("target", "?")
                    cond = b.get("condition")
                    if cond:
                        branch_strs.append(f"'{cond}' → {target}")
                    else:
                        branch_strs.append(f"→ {target}")
                parts.append(f"- **{gw_name}** ({gw_type}): {'; '.join(branch_strs)}")
            else:
                parts.append(f"- **{gw_name}** ({gw_type})")

    # 5. Handlungsanweisung
    parts.append(
        "\nBeantworte die Frage basierend auf den Dokumenten und dem gesamten Prozesskontext. "
        "Du kannst alle Aspekte des Prozesses, aller Rollen und aller Schritte beschreiben."
    )

    return "\n".join(parts)


def _get_type_hint(node_type: str) -> str:
    """Generiert kurzen Typ-Hinweis für BPMN-Node-Typen."""
    hints = {
        "userTask": "manuelle Aufgabe",
        "serviceTask": "automatisch",
        "task": "Aufgabe",
        "callActivity": "Unterprozess",
        "startEvent": "Start",
        "endEvent": "Ende",
        "exclusiveGateway": "Entscheidung",
        "parallelGateway": "parallel",
        "inclusiveGateway": "optional",
        "intermediateCatchEvent": "wartet",
        "intermediateThrowEvent": "sendet",
        "boundaryEvent": "Ereignis",
    }
    return hints.get(node_type, "")


def _get_gateway_type_name(gateway_type: str) -> str:
    """Gateway-Typ menschenlesbar."""
    names = {
        "exclusiveGateway": "Entweder-Oder",
        "parallelGateway": "Parallel",
        "inclusiveGateway": "Mehrfachauswahl",
        "eventBasedGateway": "Ereignisbasiert",
    }
    return names.get(gateway_type, "Verzweigung")


def _build_gating_hint_with_gateways(result: GatingResult) -> str:
    """
    GATING_ENABLED: Lokaler Kontext MIT Gateway-Beschreibungen.

    Fokussiert auf:
    - Aktuelle Position mit Typ-Hint
    - Direkte Vorgänger (1-2 Schritte)
    - Direkte Nachfolger mit Gateway-Branches
    - Rollenbeschränkung durch Whitelist
    """
    if not result.position:
        return ""

    parts: List[str] = []
    pos = result.position

    # 1. Rolle + Prozess
    if result.roles:
        roles_str = ", ".join(result.roles)
        parts.append(
            f"Der Nutzer fragt als **{roles_str}** im Prozess '{result.process_name}'."
        )
    else:
        parts.append(f"Kontext: Prozess '{result.process_name}'.")

    # 2. Aktuelle Position mit Typ-Hint
    if pos.current:
        current_name = pos.current.display_name()
        type_hint = _get_type_hint(pos.current.type)
        lane_info = (
            f", Zuständigkeit: {pos.current.lane_name}" if pos.current.lane_name else ""
        )
        type_info = f" ({type_hint})" if type_hint else ""

        current_str = f"**Aktueller Schritt**: '{current_name}'{type_info}{lane_info}"

        if pos.current.description:
            current_str += f". {pos.current.description}"

        parts.append(current_str)

    # 3. Vorgänger (woher kommen wir?)
    if pos.predecessors:
        pred_strs = []
        for pred in pos.predecessors[:2]:  # Max 2 Vorgänger
            pred_name = pred.display_name()
            type_hint = _get_type_hint(pred.type)
            if type_hint:
                pred_strs.append(f"'{pred_name}' ({type_hint})")
            else:
                pred_strs.append(f"'{pred_name}'")
        parts.append(f"**Vorherige Schritte**: {' → '.join(pred_strs)}")

    # 4. Nachfolger MIT Gateway-Details
    if pos.successors:
        parts.append("**Nächste Schritte**:")
        for succ in pos.successors[:4]:  # Max 4 Nachfolger
            if succ.is_gateway:
                # Gateway mit allen Branches
                gw_type = _get_gateway_type_name(succ.type)
                gw_name = succ.display_name()
                parts.append(f"  - {gw_type} '{gw_name}':")
                for branch in succ.branches:
                    cond = branch.condition_name or branch.condition or "Standard"
                    target = branch.target_name or branch.target_id
                    parts.append(f"    - Falls '{cond}': → {target}")
            else:
                succ_name = succ.display_name()
                type_hint = _get_type_hint(succ.type)
                lane_hint = f" [{succ.lane_name}]" if succ.lane_name else ""
                type_info = f" ({type_hint})" if type_hint else ""
                parts.append(f"  - '{succ_name}'{type_info}{lane_hint}")

    # 5. Handlungsanweisung (rollenspezifisch)
    parts.append(
        "\nBeantworte die Frage aus Sicht dieser Position im Prozess. "
        "Bei Entscheidungspunkten erkläre die möglichen Pfade und deren Bedingungen."
    )

    # 6. Restriktion (nur bei Whitelist-Filter)
    if pos.allowed_nodes or pos.allowed_lanes:
        parts.append(
            "Fokussiere auf die Aufgaben deiner Rolle. "
            "Erwähne Schritte anderer Rollen nur, wenn sie direkt relevant sind."
        )

    return "\n".join(parts)


def _get_process_tasks_from_neo4j(process_id: str) -> Dict[str, Any]:
    """
    Holt ALLE Task-Namen und Lane-Zuordnungen aus Neo4j.

    Returns:
        {
            "all_task_names": ["Antrag erstellen", "Genehmigung prüfen", ...],
            "lane_task_mapping": {
                "Antragsteller": ["Antrag erstellen", ...],
                "Vorgesetzter": ["Genehmigung erteilen", ...],
            }
        }
    """
    if not process_id:
        return {"all_task_names": [], "lane_task_mapping": {}}

    try:
        from app.core.clients import get_neo4j

        driver = get_neo4j()

        with driver.session() as s:
            result = s.run(
                """
                MATCH (p:Process {xmlId:$pid})-[:CONTAINS]->(n:Node)
                WHERE NOT n.type CONTAINS 'Gateway' 
                  AND NOT n.type CONTAINS 'Event'
                OPTIONAL MATCH (l:Lane)-[:CONTAINS]->(n)
                RETURN n.name AS task_name, 
                       n.type AS task_type,
                       l.name AS lane_name
                """,
                pid=process_id,
            ).data()

        all_tasks: List[str] = []
        lane_mapping: Dict[str, List[str]] = {}

        for row in result:
            task_name = row.get("task_name")
            lane_name = row.get("lane_name") or "Unbekannt"

            if task_name:
                all_tasks.append(task_name)
                if lane_name not in lane_mapping:
                    lane_mapping[lane_name] = []
                if task_name not in lane_mapping[lane_name]:
                    lane_mapping[lane_name].append(task_name)

        return {
            "all_task_names": list(set(all_tasks)),
            "lane_task_mapping": lane_mapping,
        }

    except Exception as e:
        logger.info(f"Neo4j-Lookup für Prozess {process_id} fehlgeschlagen: {e}")
        return {"all_task_names": [], "lane_task_mapping": {}}
