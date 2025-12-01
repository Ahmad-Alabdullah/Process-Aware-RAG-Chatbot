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
                s.run(
                    """
                    MATCH (s:Node {xmlId:$src})
                    MATCH (t:Node {xmlId:$tgt})
                    MERGE (s)-[:FLOWS_TO {xmlId:$fid}]->(t)
                """,
                    fid=fid,
                    src=src,
                    tgt=tgt,
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
    max_depth: int = 2,
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

            // ...rest of query...
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
