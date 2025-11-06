from __future__ import annotations
from typing import Dict, List, Tuple
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
