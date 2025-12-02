from __future__ import annotations
from typing import Any, Dict, List, Tuple
from datetime import datetime
import uuid
from defusedxml import ElementTree as ET

from app.core.clients import get_neo4j
from app.services.whitelist import create_default_whitelist


# ---- XML helper ----
def _local(tag: str) -> str:
    return (
        tag.split("}", 1)[-1]
        if "}" in tag
        else (tag.split(":", 1)[-1] if ":" in tag else tag)
    )


def _attr(el, name: str, default: str | None = None) -> str | None:
    return el.attrib.get(name, default)


# BPMN FlowNode-Tags
_NODE_TAGS = {
    "task",
    "userTask",
    "serviceTask",
    "scriptTask",
    "manualTask",
    "receiveTask",
    "sendTask",
    "businessRuleTask",
    "callActivity",
    "subProcess",
    "startEvent",
    "endEvent",
    "intermediateCatchEvent",
    "intermediateThrowEvent",
    "boundaryEvent",
    "exclusiveGateway",
    "parallelGateway",
    "inclusiveGateway",
    "eventBasedGateway",
}


def import_bpmn_xml_and_whitelist(
    xml_text: str,
    filename: str,
    store_raw: bool = True,
    auto_whitelist: bool = True,
) -> Dict:
    """
    Validiert BPMN-2.0, speichert Definitions/Prozesse/Knoten/Kanten/Lanes in Neo4j
    und erzeugt optional eine Whitelist je Lane/Prozess.
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        raise ValueError(f"Ungültiges XML: {e}")

    if _local(root.tag) != "definitions":
        # BPMN-2.0 XML muss <bpmn:definitions …> als Wurzel haben
        raise ValueError("Invalid BPMN XML (missing <definitions>).")

    processes = root.findall(".//{*}process")
    if not processes:
        raise ValueError("Kein <process> in der Datei gefunden.")

    has_di = root.find(".//{*}BPMNDiagram") is not None
    defs_id = _attr(root, "id") or f"defs_{uuid.uuid4().hex[:10]}"
    defs_name = _attr(root, "name") or filename
    target_ns = _attr(root, "targetNamespace") or ""

    driver = get_neo4j()
    total_nodes = 0
    total_flows = 0
    total_lanes = 0
    proc_infos: List[Dict] = []

    with driver.session() as s:
        # Constraints (idempotent)
        try:
            s.run(
                "CREATE CONSTRAINT bpmn_defs IF NOT EXISTS FOR (d:BPMN) REQUIRE d.definitionId IS UNIQUE"
            )
            s.run(
                "CREATE CONSTRAINT bpmn_proc IF NOT EXISTS FOR (p:Process) REQUIRE p.xmlId IS UNIQUE"
            )
            s.run(
                "CREATE CONSTRAINT bpmn_node IF NOT EXISTS FOR (n:Node) REQUIRE n.xmlId IS UNIQUE"
            )
            s.run(
                "CREATE CONSTRAINT bpmn_lane IF NOT EXISTS FOR (l:Lane) REQUIRE l.xmlId IS UNIQUE"
            )
            s.run(
                "CREATE CONSTRAINT wl_defs  IF NOT EXISTS FOR (w:Whitelist) REQUIRE w.definitionId IS UNIQUE"
            )
        except Exception:
            pass

        # Definitions-Knoten
        s.run(
            """
            MERGE (d:BPMN {definitionId:$defs})
            SET d.name=$name, d.targetNamespace=$tns, d.hasDiagram=$has_di,
                d.filename=$fname, d.updatedAt=$ts
        """,
            defs=defs_id,
            name=defs_name,
            tns=target_ns,
            has_di=bool(has_di),
            fname=filename,
            ts=datetime.utcnow().isoformat(),
        )
        if store_raw:
            s.run(
                "MATCH (d:BPMN {definitionId:$defs}) SET d.xml=$xml",
                defs=defs_id,
                xml=xml_text,
            )

        # Prozesse + enthaltene Elemente
        for p in processes:
            pid = _attr(p, "id") or f"proc_{uuid.uuid4().hex[:10]}"
            pname = _attr(p, "name") or ""
            s.run(
                """
                MERGE (pr:Process {xmlId:$pid})
                SET pr.name=$pname
                WITH pr
                MATCH (d:BPMN {definitionId:$defs})
                MERGE (d)-[:CONTAINS]->(pr)
            """,
                pid=pid,
                pname=pname,
                defs=defs_id,
            )

            # Knoten innerhalb dieses Prozesses
            nodes: List[Tuple[str, str, str]] = []
            for el in p.findall(".//*"):
                t = _local(el.tag)
                if t in _NODE_TAGS:
                    nid = _attr(el, "id") or f"gen_{uuid.uuid4().hex[:10]}"
                    nname = _attr(el, "name") or ""
                    nodes.append((nid, nname, t))
            total_nodes += len(nodes)

            for nid, nname, ntype in nodes:
                s.run(
                    """
                    MERGE (n:Node {xmlId:$nid})
                    SET n.name=$nname, n.type=$ntype
                    WITH n
                    MATCH (pr:Process {xmlId:$pid})
                    MERGE (pr)-[:CONTAINS]->(n)
                """,
                    nid=nid,
                    nname=nname,
                    ntype=ntype,
                    pid=pid,
                )

            # Sequence Flows des Prozesses
            flows: List[Tuple[str, str, str]] = []
            for sf in p.findall(".//{*}sequenceFlow"):
                fid = _attr(sf, "id") or f"sf_{uuid.uuid4().hex[:10]}"
                src = _attr(sf, "sourceRef")
                tgt = _attr(sf, "targetRef")
                if src and tgt:
                    flows.append((fid, src, tgt))
            total_flows += len(flows)

            for fid, src, tgt in flows:
                sf_element = p.find(f".//*[@id='{fid}']")
                condition_expr = None
                condition_name = None

                if sf_element is not None:
                    # conditionExpression Element
                    cond_el = sf_element.find("{*}conditionExpression")
                    if cond_el is not None and cond_el.text:
                        condition_expr = cond_el.text.strip()
                    # name Attribut (oft für Ja/Nein Labels)
                    condition_name = _attr(sf_element, "name")

                s.run(
                    """
                    MATCH (s:Node {xmlId:$src})
                    MATCH (t:Node {xmlId:$tgt})
                    MERGE (s)-[r:FLOWS_TO {xmlId:$fid}]->(t)
                    SET r.conditionExpression = $cond_expr,
                        r.name = $cond_name
                """,
                    fid=fid,
                    src=src,
                    tgt=tgt,
                    cond_expr=condition_expr,
                    cond_name=condition_name,
                )

            # Lanes (mit flowNodeRef → Zuordnung)
            lanes: List[Tuple[str, str]] = []
            lane_members: List[Tuple[str, str]] = []
            for lane in p.findall(".//{*}lane"):
                lid = _attr(lane, "id") or f"lane_{uuid.uuid4().hex[:10]}"
                lname = _attr(lane, "name") or ""
                lanes.append((lid, lname))
                for ref in lane.findall(".//{*}flowNodeRef"):
                    if ref.text:
                        lane_members.append((lid, ref.text.strip()))
            total_lanes += len(lanes)

            for lid, lname in lanes:
                s.run(
                    "MERGE (l:Lane {xmlId:$lid}) SET l.name=$lname",
                    lid=lid,
                    lname=lname,
                )
                s.run(
                    """
                    MATCH (d:BPMN {definitionId:$defs})
                    MATCH (pr:Process {xmlId:$pid})
                    MATCH (l:Lane {xmlId:$lid})
                    MERGE (d)-[:CONTAINS]->(l)
                    MERGE (pr)-[:HAS_LANE]->(l)
                """,
                    defs=defs_id,
                    pid=pid,
                    lid=lid,
                )

            for lid, ref in lane_members:
                s.run(
                    """
                    MATCH (l:Lane {xmlId:$lid})
                    MATCH (n:Node {xmlId:$ref})
                    MERGE (l)-[:CONTAINS]->(n)
                """,
                    lid=lid,
                    ref=ref,
                )

            proc_infos.append({"id": pid, "name": pname})

    # Auto-Whitelist nach dem Speichern
    wl_counts = {"rules": 0, "lanes": 0}
    if auto_whitelist:
        wl_counts = create_default_whitelist(definition_id=defs_id)

    return {
        "definitionId": defs_id,
        "file": filename,
        "processes": proc_infos,
        "nodes": total_nodes,
        "flows": total_flows,
        "lanes": total_lanes,
        "hasDiagram": bool(has_di),
        "whitelist": wl_counts,
    }


def list_definitions() -> List[Dict[str, Any]]:
    driver = get_neo4j()
    with driver.session() as s:
        rows = s.run(
            """
            MATCH (d:BPMN)
            OPTIONAL MATCH (d)-[:CONTAINS]->(p:Process)
            WITH d, collect({id:p.xmlId, name:p.name}) AS processes
            RETURN d.definitionId AS id,
                   d.name AS name,
                   d.filename AS filename,
                   size(processes) AS processCount,
                   processes
            ORDER BY name, id
            """
        ).data()
    return rows


def list_process_nodes_lanes(process_id: str) -> Dict[str, Any]:
    driver = get_neo4j()
    with driver.session() as s:
        data = s.run(
            """
            MATCH (p:Process {xmlId:$pid})
            OPTIONAL MATCH (p)-[:HAS_LANE]->(l:Lane)
            OPTIONAL MATCH (p)-[:CONTAINS]->(n:Node)
            OPTIONAL MATCH (l)-[:CONTAINS]->(n2:Node)
            WITH p,
                 collect(DISTINCT {id:l.xmlId, name:l.name}) AS lanes,
                 collect(DISTINCT {
                     id:n.xmlId,
                     name:n.name,
                     type:n.type
                 }) AS nodes1,
                 collect(DISTINCT {
                     id:n2.xmlId,
                     name:n2.name,
                     type:n2.type,
                     laneId: l.xmlId
                 }) AS nodes2
            WITH p, lanes,
                 apoc.coll.toSet(nodes1 + nodes2) AS nodes
            RETURN p.xmlId AS id,
                   p.name AS name,
                   lanes,
                   nodes
            """,
            pid=process_id,
        ).single()
    if not data:
        return {}
    return data


def process_graph(process_id: str) -> Dict[str, Any]:
    driver = get_neo4j()
    with driver.session() as s:
        nodes = s.run(
            """
            MATCH (p:Process {xmlId:$pid})-[:CONTAINS]->(n:Node)
            OPTIONAL MATCH (l:Lane)-[:CONTAINS]->(n)
            RETURN n.xmlId AS id, n.name AS name, n.type AS type,
                   l.xmlId AS laneId
            """,
            pid=process_id,
        ).data()
        edges = s.run(
            """
            MATCH (p:Process {xmlId:$pid})-[:CONTAINS]->(:Node)-[f:FLOWS_TO]->(m:Node)
            RETURN f.xmlId AS id,
                   startNode(f).xmlId AS source,
                   endNode(f).xmlId AS target
            """,
            pid=process_id,
        ).data()
    return {"nodes": nodes, "edges": edges}


def lane_and_task_labels(
    process_id: str, lane_ids: List[str], node_ids: List[str]
) -> Dict[str, List[str]]:
    driver = get_neo4j()
    with driver.session() as s:
        lanes = s.run(
            """
            MATCH (p:Process {xmlId:$pid})-[:HAS_LANE]->(l:Lane)
            WHERE l.xmlId IN $lane_ids
            RETURN l.xmlId AS id, l.name AS name
            """,
            pid=process_id,
            lane_ids=lane_ids,
        ).data()

        tasks = s.run(
            """
            MATCH (p:Process {xmlId:$pid})-[:CONTAINS]->(n:Node)
            WHERE n.xmlId IN $node_ids
            RETURN n.xmlId AS id, n.name AS name, n.type AS type
            """,
            pid=process_id,
            node_ids=node_ids,
        ).data()
    return {"lanes": lanes, "tasks": tasks}


def local_process_view(
    process_id: str,
    current_node_id: str,
    max_depth: int = 3,
) -> Dict[str, Any]:
    """
    Liefert eine lokale Ansicht rund um den aktuellen BPMN-Knoten:
    - current: aktueller Node inkl. Lane
    - predecessors: Vorgänger (bis max_depth Hops)
    - successors: Nachfolger (bis max_depth Hops)

    Jede Node-Struktur enthält: {id, name, type, laneId, laneName}.
    """
    driver = get_neo4j()
    with driver.session() as s:
        query = f"""
            MATCH (p:Process {{xmlId:$pid}})-[:CONTAINS]->(center:Node {{xmlId:$nid}})

            // Nachfolger sammeln
            OPTIONAL MATCH (center)-[:FLOWS_TO*1..{max_depth}]->(succ:Node)
            WITH center, collect(DISTINCT succ) AS succs

            // Vorgänger sammeln
            OPTIONAL MATCH (pred:Node)-[:FLOWS_TO*1..{max_depth}]->(center)
            WITH center,
                 coalesce(succs, []) AS succs,
                 collect(DISTINCT pred) AS preds

            // Lane-Zuordnung für Center-Node
            OPTIONAL MATCH (lc:Lane)-[:CONTAINS]->(center)
            WITH center, succs, preds, lc

            // Vorgänger-Lanes
            UNWIND coalesce(preds, []) AS pn
            OPTIONAL MATCH (lp:Lane)-[:CONTAINS]->(pn)
            WITH center, succs,
                 collect(DISTINCT {{
                     id: pn.xmlId,
                     name: pn.name,
                     type: pn.type,
                     laneId: lp.xmlId,
                     laneName: lp.name
                 }}) AS pred_nodes

            UNWIND coalesce(succs, []) AS sn
            OPTIONAL MATCH (ls:Lane)-[:CONTAINS]->(sn)
            WITH center, pred_nodes,
                 collect(DISTINCT {{
                     id: sn.xmlId,
                     name: sn.name,
                     type: sn.type,
                     laneId: ls.xmlId,
                     laneName: ls.name
                 }}) AS succ_nodes

            OPTIONAL MATCH (lc:Lane)-[:CONTAINS]->(center)
            RETURN {{
                id: center.xmlId,
                name: center.name,
                type: center.type,
                laneId: lc.xmlId,
                laneName: lc.name
            }} AS current,
            pred_nodes AS predecessors,
            succ_nodes AS successors
            """
        rec = s.run(query, pid=process_id, nid=current_node_id).single()

    if not rec:
        return {}
    return rec


def local_process_view_with_gateways(
    process_id: str,
    current_node_id: str,
    max_depth: int = 2,
) -> Dict[str, Any]:
    """
    Erweiterte lokale Ansicht mit Gateway-Auflösung.

    Wenn der nächste Schritt ein Gateway ist, werden die ausgehenden
    Pfade mit Bedingungen (conditionExpression) und Zielknoten zurückgegeben.

    Returns:
        {
            "current": {...},
            "predecessors": [...],
            "successors": [
                {..., "is_gateway": True, "branches": [...]},
                {..., "is_gateway": False}
            ]
        }
    """
    driver = get_neo4j()
    with driver.session() as s:
        # Aktueller Knoten mit Lane
        current_rec = s.run(
            """
            MATCH (p:Process {xmlId:$pid})-[:CONTAINS]->(n:Node {xmlId:$nid})
            OPTIONAL MATCH (l:Lane)-[:CONTAINS]->(n)
            RETURN {
                id: n.xmlId,
                name: n.name,
                type: n.type,
                description: n.description,
                laneId: l.xmlId,
                laneName: l.name
            } AS current
            """,
            pid=process_id,
            nid=current_node_id,
        ).single()

        if not current_rec:
            return {}

        # Direkte Nachfolger inkl. Gateways
        succ_recs = s.run(
            """
            MATCH (p:Process {xmlId:$pid})-[:CONTAINS]->(n:Node {xmlId:$nid})
            MATCH (n)-[f:FLOWS_TO]->(succ:Node)
            OPTIONAL MATCH (ls:Lane)-[:CONTAINS]->(succ)
            RETURN {
                id: succ.xmlId,
                name: succ.name,
                type: succ.type,
                description: succ.description,
                laneId: ls.xmlId,
                laneName: ls.name,
                condition: f.conditionExpression,
                conditionName: f.name
            } AS successor
            """,
            pid=process_id,
            nid=current_node_id,
        ).data()

        successors = []
        for rec in succ_recs:
            succ = dict(rec["successor"])
            succ_type = succ.get("type", "")

            # Prüfe ob Gateway
            is_gateway = "Gateway" in succ_type
            succ["is_gateway"] = is_gateway

            if is_gateway:
                # Hole Gateway-Branches (ausgehende Pfade)
                branch_recs = s.run(
                    """
                    MATCH (gw:Node {xmlId:$gwid})-[f:FLOWS_TO]->(target:Node)
                    OPTIONAL MATCH (lt:Lane)-[:CONTAINS]->(target)
                    RETURN {
                        id: target.xmlId,
                        name: target.name,
                        type: target.type,
                        description: target.description,
                        laneId: lt.xmlId,
                        laneName: lt.name,
                        condition: f.conditionExpression,
                        conditionName: f.name
                    } AS branch
                    """,
                    gwid=succ["id"],
                ).data()
                succ["branches"] = [dict(b["branch"]) for b in branch_recs]

            successors.append(succ)

        # Vorgänger (ohne Gateway-Details)
        pred_recs = s.run(
            f"""
            MATCH (p:Process {{xmlId:$pid}})-[:CONTAINS]->(n:Node {{xmlId:$nid}})
            MATCH (pred:Node)-[:FLOWS_TO*1..{max_depth}]->(n)
            OPTIONAL MATCH (lp:Lane)-[:CONTAINS]->(pred)
            RETURN DISTINCT {{
                id: pred.xmlId,
                name: pred.name,
                type: pred.type,
                description: pred.description,
                laneId: lp.xmlId,
                laneName: lp.name
            }} AS predecessor
            LIMIT 5
            """,
            pid=process_id,
            nid=current_node_id,
        ).data()

        predecessors = [dict(p["predecessor"]) for p in pred_recs]

    return {
        "current": dict(current_rec["current"]) if current_rec else None,
        "predecessors": predecessors,
        "successors": successors,
    }


def get_process_overview(process_id: str) -> Dict[str, Any]:
    """
    Liefert groben Prozessüberblick inkl. Gateways.
    """
    driver = get_neo4j()
    with driver.session() as s:
        result = s.run(
            """
            MATCH (p:Process {xmlId:$pid})
            OPTIONAL MATCH (p)-[:HAS_LANE]->(l:Lane)
            OPTIONAL MATCH (p)-[:CONTAINS]->(n:Node)
            WITH p,
                 collect(DISTINCT {id: l.xmlId, name: l.name}) AS lanes,
                 collect(DISTINCT {
                     id: n.xmlId, 
                     name: n.name, 
                     type: n.type,
                     description: n.description
                 }) AS nodes
            RETURN p.name AS name, lanes, nodes
            """,
            pid=process_id,
        ).single()

    if not result:
        return {}

    return {
        "name": result["name"],
        "lanes": [l for l in result["lanes"] if l.get("id")],
        "nodes": [n for n in result["nodes"] if n.get("id")],
    }


def get_process_overview_full(process_id: str) -> Dict[str, Any]:
    """
    Liefert VOLLSTÄNDIGEN Prozessüberblick inkl. aller Beziehungen.

    Für PROCESS_CONTEXT Modus (Ablation-Study):
    - Alle Lanes mit zugeordneten Tasks
    - Alle Nodes mit Typ-Hints
    - Alle Sequence Flows (Beziehungen)
    - Alle Gateway-Branches

    Returns:
        {
            "name": "Dienstreiseantrag",
            "lanes": [
                {
                    "id": "Lane_1",
                    "name": "Antragsteller",
                    "nodes": [
                        {"id": "Task_1", "name": "Antrag erstellen", "type": "userTask"},
                        ...
                    ]
                },
                ...
            ],
            "nodes_without_lane": [...],  # Falls Tasks keiner Lane zugeordnet
            "flows": [
                {"from": "Task_1", "to": "Gateway_1", "condition": null},
                {"from": "Gateway_1", "to": "Task_2", "condition": "Genehmigt"},
                ...
            ],
            "gateways": [
                {
                    "id": "Gateway_1",
                    "name": "Genehmigung?",
                    "type": "exclusiveGateway",
                    "branches": [
                        {"target": "Task_2", "condition": "Ja"},
                        {"target": "Task_3", "condition": "Nein"}
                    ]
                }
            ]
        }
    """
    driver = get_neo4j()
    with driver.session() as s:
        # 1. Prozess-Name
        proc_rec = s.run(
            "MATCH (p:Process {xmlId:$pid}) RETURN p.name AS name",
            pid=process_id,
        ).single()

        if not proc_rec:
            return {}

        process_name = proc_rec["name"] or process_id

        # 2. Alle Lanes mit ihren Nodes
        lanes_data = s.run(
            """
            MATCH (p:Process {xmlId:$pid})-[:HAS_LANE]->(l:Lane)
            OPTIONAL MATCH (l)-[:CONTAINS]->(n:Node)
            WITH l, collect({
                id: n.xmlId,
                name: n.name,
                type: n.type,
                description: n.description
            }) AS nodes
            RETURN l.xmlId AS id, l.name AS name, nodes
            ORDER BY l.name
            """,
            pid=process_id,
        ).data()

        lanes = []
        lane_node_ids = set()
        for lane in lanes_data:
            lane_nodes = [n for n in lane["nodes"] if n.get("id")]
            lane_node_ids.update(n["id"] for n in lane_nodes)
            lanes.append(
                {
                    "id": lane["id"],
                    "name": lane["name"],
                    "nodes": lane_nodes,
                }
            )

        # 3. Nodes ohne Lane-Zuordnung
        all_nodes_data = s.run(
            """
            MATCH (p:Process {xmlId:$pid})-[:CONTAINS]->(n:Node)
            RETURN n.xmlId AS id, n.name AS name, n.type AS type, n.description AS description
            """,
            pid=process_id,
        ).data()

        nodes_without_lane = [
            n for n in all_nodes_data if n["id"] not in lane_node_ids and n.get("id")
        ]

        # 4. Alle Sequence Flows (Beziehungen)
        flows_data = s.run(
            """
            MATCH (p:Process {xmlId:$pid})-[:CONTAINS]->(src:Node)-[f:FLOWS_TO]->(tgt:Node)
            RETURN src.xmlId AS from_id, 
                   src.name AS from_name,
                   tgt.xmlId AS to_id,
                   tgt.name AS to_name,
                   f.conditionExpression AS condition,
                   f.name AS condition_name
            """,
            pid=process_id,
        ).data()

        flows = [
            {
                "from": f["from_name"] or f["from_id"],
                "to": f["to_name"] or f["to_id"],
                "condition": f["condition_name"] or f["condition"],
            }
            for f in flows_data
        ]

        # 5. Gateways mit Branches
        gateways_data = s.run(
            """
            MATCH (p:Process {xmlId:$pid})-[:CONTAINS]->(gw:Node)
            WHERE gw.type CONTAINS 'Gateway'
            OPTIONAL MATCH (gw)-[f:FLOWS_TO]->(target:Node)
            WITH gw, collect({
                target_id: target.xmlId,
                target_name: target.name,
                condition: f.conditionExpression,
                condition_name: f.name
            }) AS branches
            RETURN gw.xmlId AS id, 
                   gw.name AS name, 
                   gw.type AS type,
                   branches
            """,
            pid=process_id,
        ).data()

        gateways = [
            {
                "id": gw["id"],
                "name": gw["name"],
                "type": gw["type"],
                "branches": [
                    {
                        "target": b["target_name"] or b["target_id"],
                        "condition": b["condition_name"] or b["condition"],
                    }
                    for b in gw["branches"]
                    if b.get("target_id")
                ],
            }
            for gw in gateways_data
        ]

    return {
        "name": process_name,
        "lanes": lanes,
        "nodes_without_lane": nodes_without_lane,
        "flows": flows,
        "gateways": gateways,
    }


def delete_all_bpmn_data() -> Dict[str, int]:
    """
    Löscht ALLE BPMN-Daten aus Neo4j.

    Returns:
        Dict mit Anzahl gelöschter Elemente pro Typ
    """
    driver = get_neo4j()
    counts = {}

    with driver.session() as s:
        # Whitelists + Rules zuerst (wegen Beziehungen)
        result = s.run(
            """
            MATCH (r:WhitelistRule)
            WITH count(r) AS cnt
            MATCH (r:WhitelistRule) DETACH DELETE r
            RETURN cnt
            """
        ).single()
        counts["whitelist_rules"] = result["cnt"] if result else 0

        result = s.run(
            """
            MATCH (w:Whitelist)
            WITH count(w) AS cnt
            MATCH (w:Whitelist) DETACH DELETE w
            RETURN cnt
            """
        ).single()
        counts["whitelists"] = result["cnt"] if result else 0

        # Participants
        result = s.run(
            """
            MATCH (p:Participant)
            WITH count(p) AS cnt
            MATCH (p:Participant) DETACH DELETE p
            RETURN cnt
            """
        ).single()
        counts["participants"] = result["cnt"] if result else 0

        # Nodes
        result = s.run(
            """
            MATCH (n:Node)
            WITH count(n) AS cnt
            MATCH (n:Node) DETACH DELETE n
            RETURN cnt
            """
        ).single()
        counts["nodes"] = result["cnt"] if result else 0

        # Lanes
        result = s.run(
            """
            MATCH (l:Lane)
            WITH count(l) AS cnt
            MATCH (l:Lane) DETACH DELETE l
            RETURN cnt
            """
        ).single()
        counts["lanes"] = result["cnt"] if result else 0

        # Processes
        result = s.run(
            """
            MATCH (p:Process)
            WITH count(p) AS cnt
            MATCH (p:Process) DETACH DELETE p
            RETURN cnt
            """
        ).single()
        counts["processes"] = result["cnt"] if result else 0

        # BPMN Definitions
        result = s.run(
            """
            MATCH (d:BPMN)
            WITH count(d) AS cnt
            MATCH (d:BPMN) DETACH DELETE d
            RETURN cnt
            """
        ).single()
        counts["definitions"] = result["cnt"] if result else 0

    return counts


def delete_bpmn_by_definition(definition_id: str) -> Dict[str, Any]:
    """
    Löscht eine spezifische BPMN-Definition und alle zugehörigen Daten.

    Args:
        definition_id: Die definitionId der zu löschenden Definition

    Returns:
        Dict mit Anzahl gelöschter Elemente und found-Status
    """
    driver = get_neo4j()
    counts = {"found": False}

    with driver.session() as s:
        # Prüfen ob Definition existiert
        exists = s.run(
            "MATCH (d:BPMN {definitionId:$defId}) RETURN count(d) AS cnt",
            defId=definition_id,
        ).single()

        if not exists or exists["cnt"] == 0:
            return {"found": False}

        counts["found"] = True
        counts["definition_id"] = definition_id

        # WhitelistRules dieser Definition
        result = s.run(
            """
            MATCH (r:WhitelistRule {definitionId:$defId})
            WITH count(r) AS cnt
            MATCH (r:WhitelistRule {definitionId:$defId}) DETACH DELETE r
            RETURN cnt
            """,
            defId=definition_id,
        ).single()
        counts["whitelist_rules"] = result["cnt"] if result else 0

        # Whitelist dieser Definition
        result = s.run(
            """
            MATCH (w:Whitelist {definitionId:$defId})
            WITH count(w) AS cnt
            MATCH (w:Whitelist {definitionId:$defId}) DETACH DELETE w
            RETURN cnt
            """,
            defId=definition_id,
        ).single()
        counts["whitelists"] = result["cnt"] if result else 0

        # Nodes der Processes dieser Definition
        result = s.run(
            """
            MATCH (d:BPMN {definitionId:$defId})-[:CONTAINS]->(p:Process)-[:CONTAINS]->(n:Node)
            WITH count(n) AS cnt, collect(n) AS nodes
            UNWIND nodes AS n
            DETACH DELETE n
            RETURN cnt
            """,
            defId=definition_id,
        ).single()
        counts["nodes"] = result["cnt"] if result else 0

        # Lanes der Processes dieser Definition
        result = s.run(
            """
            MATCH (d:BPMN {definitionId:$defId})-[:CONTAINS]->(p:Process)-[:HAS_LANE]->(l:Lane)
            WITH count(l) AS cnt, collect(l) AS lanes
            UNWIND lanes AS l
            DETACH DELETE l
            RETURN cnt
            """,
            defId=definition_id,
        ).single()
        counts["lanes"] = result["cnt"] if result else 0

        # Auch Lanes die direkt an Definition hängen
        result = s.run(
            """
            MATCH (d:BPMN {definitionId:$defId})-[:CONTAINS]->(l:Lane)
            WITH count(l) AS cnt, collect(l) AS lanes
            UNWIND lanes AS l
            DETACH DELETE l
            RETURN cnt
            """,
            defId=definition_id,
        ).single()
        counts["lanes"] = counts.get("lanes", 0) + (result["cnt"] if result else 0)

        # Participants dieser Definition
        result = s.run(
            """
            MATCH (d:BPMN {definitionId:$defId})-[:HAS_PARTICIPANT]->(pa:Participant)
            WITH count(pa) AS cnt, collect(pa) AS parts
            UNWIND parts AS pa
            DETACH DELETE pa
            RETURN cnt
            """,
            defId=definition_id,
        ).single()
        counts["participants"] = result["cnt"] if result else 0

        # Processes dieser Definition
        result = s.run(
            """
            MATCH (d:BPMN {definitionId:$defId})-[:CONTAINS]->(p:Process)
            WITH count(p) AS cnt, collect(p) AS procs
            UNWIND procs AS p
            DETACH DELETE p
            RETURN cnt
            """,
            defId=definition_id,
        ).single()
        counts["processes"] = result["cnt"] if result else 0

        # Definition selbst
        s.run(
            "MATCH (d:BPMN {definitionId:$defId}) DETACH DELETE d", defId=definition_id
        )
        counts["definitions"] = 1

    return counts
