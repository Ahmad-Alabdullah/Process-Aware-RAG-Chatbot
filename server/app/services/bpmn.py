from __future__ import annotations
from typing import Dict, List, Tuple
from datetime import datetime
import uuid

from defusedxml import ElementTree as ET
from app.core.clients import get_neo4j


# helper functions
def _local(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _attr(el, name: str, default: str | None = None) -> str | None:
    return el.attrib.get(name, default)


# Kernelemente eines BPMN 2.0 Modells
_NODE_TAGS = {
    "process",
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


def import_bpmn_xml(xml_text: str, filename: str, store_raw: bool = True) -> Dict:
    """
    Validiert BPMN-2.0-Struktur, extrahiert Prozesse/Knoten/Kanten,
    speichert alles in Neo4j und gibt eine kurze Inventur zurück.
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        raise ValueError(f"Ungültiges XML: {e}")

    if _local(root.tag) != "definitions":
        # Wurzel MUSS <bpmn:definitions> sein (BPMN 2.0 Core Structure)
        raise ValueError("Invalid BPMN XML (missing <definitions>).")

    # Prozesse sammeln
    processes = root.findall(".//{*}process")
    if not processes:
        raise ValueError("Kein <process> in der Datei gefunden.")

    # BPMN-DI vorhanden?
    has_di = root.find(".//{*}BPMNDiagram") is not None

    # Alle Flow-Nodes (Knoten) und SequenceFlows (Kanten) einsammeln
    nodes: List[Tuple[str, str, str]] = []  # (id, name, type)
    for el in root.findall(".//*"):
        t = _local(el.tag)
        if t in _NODE_TAGS:
            el_id = _attr(el, "id")
            if not el_id:
                # falls ein Modell ohne IDs
                el_id = f"gen_{uuid.uuid4().hex[:12]}"
            nodes.append((el_id, _attr(el, "name") or "", t))

    flows: List[Tuple[str, str, str]] = []  # (id, sourceRef, targetRef)
    for sf in root.findall(".//{*}sequenceFlow"):
        sf_id = _attr(sf, "id") or f"sf_{uuid.uuid4().hex[:12]}"
        src = _attr(sf, "sourceRef")
        tgt = _attr(sf, "targetRef")
        if src and tgt:
            flows.append((sf_id, src, tgt))

    # Lane-Zuordnungen
    lanes: List[Tuple[str, str]] = []  # (laneId, name)
    lane_members: List[Tuple[str, str]] = []  # (laneId, flowNodeRef)
    for lane in root.findall(".//{*}lane"):
        lid = _attr(lane, "id") or f"lane_{uuid.uuid4().hex[:12]}"
        lanes.append((lid, _attr(lane, "name") or ""))
        for ref in lane.findall(".//{*}flowNodeRef"):
            if ref.text:
                lane_members.append((lid, ref.text.strip()))

    # Collaboration / Participants (Pools) (optional)
    participants: List[Tuple[str, str]] = []  # (participantId, processRef)
    for p in root.findall(".//{*}participant"):
        pid = _attr(p, "id") or f"part_{uuid.uuid4().hex[:12]}"
        pref = _attr(p, "processRef")
        if pref:
            participants.append((pid, pref))

    # Definitions-Metadaten
    defs_id = _attr(root, "id") or f"defs_{uuid.uuid4().hex[:12]}"
    defs_name = _attr(root, "name") or filename
    target_ns = _attr(root, "targetNamespace") or ""

    # ---- Persistenz in Neo4j ----
    driver = get_neo4j()
    with driver.session() as s:
        # Constraints einmalig probieren (idempotent)
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
        except Exception:
            pass

        # Definitions-Knoten
        s.run(
            """
            MERGE (d:BPMN {definitionId:$defs_id})
            SET d.name=$name, d.targetNamespace=$tns, d.hasDiagram=$has_di,
                d.filename=$fname, d.updatedAt=$ts
            """,
            defs_id=defs_id,
            name=defs_name,
            tns=target_ns,
            has_di=bool(has_di),
            fname=filename,
            ts=datetime.utcnow().isoformat(),
        )
        if store_raw:
            s.run(
                """
                MATCH (d:BPMN {definitionId:$defs_id})
                SET d.xml=$xml
                """,
                defs_id=defs_id,
                xml=xml_text,
            )

        # Prozesse
        for p in processes:
            pid = _attr(p, "id") or f"proc_{uuid.uuid4().hex[:12]}"
            pname = _attr(p, "name") or ""
            s.run(
                """
                MERGE (pr:Process {xmlId:$pid})
                SET pr.name=$pname
                WITH pr
                MATCH (d:BPMN {definitionId:$defs_id})
                MERGE (d)-[:CONTAINS]->(pr)
            """,
                pid=pid,
                pname=pname,
                defs_id=defs_id,
            )

        # Teilnehmer (Pools) ↔ Prozesse
        for part_id, proc_ref in participants:
            s.run(
                """
                MERGE (pa:Participant {xmlId:$part_id})
                SET pa.processRef=$proc_ref
                WITH pa
                MATCH (pr:Process {xmlId:$proc_ref})
                MERGE (pa)-[:PARTICIPATES_IN]->(pr)
                WITH pa
                MATCH (d:BPMN {definitionId:$defs_id})
                MERGE (d)-[:HAS_PARTICIPANT]->(pa)
            """,
                part_id=part_id,
                proc_ref=proc_ref,
                defs_id=defs_id,
            )

        # Knoten
        for nid, nname, ntype in nodes:
            s.run(
                """
                MERGE (n:Node {xmlId:$nid})
                SET n.name=$nname, n.type=$ntype
                WITH n
                // Über processRef herstellen, falls es eine direkte Elternschaft gibt
                OPTIONAL MATCH (pr:Process)-[:CONTAINS]->(:Node {xmlId:$nid})
                RETURN n
            """,
                nid=nid,
                nname=nname,
                ntype=ntype,
            )

        # Kanten (SequenceFlows)
        for fid, src, tgt in flows:
            s.run(
                """
                MATCH (s:Node {xmlId:$src})
                MATCH (t:Node {xmlId:$tgt})
                MERGE (s)-[r:FLOWS_TO {xmlId:$fid}]->(t)
            """,
                fid=fid,
                src=src,
                tgt=tgt,
            )

        # Lanes & Zuordnung
        for lid, lname in lanes:
            s.run("MERGE (l:Lane {xmlId:$lid}) SET l.name=$lname", lid=lid, lname=lname)
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

        # BPMN->Process Kanten (fallback): hänge alle Nodes an Definitions/Prozess,
        # wenn eine eindeutige processRef aus dem XML abggeiten werden kann.
        for p in processes:
            pid = _attr(p, "id")
            if not pid:
                continue
            s.run(
                """
                MATCH (pr:Process {xmlId:$pid})
                MATCH (d:BPMN {definitionId:$defs_id})
                MERGE (d)-[:CONTAINS]->(pr)
            """,
                pid=pid,
                defs_id=defs_id,
            )

    return {
        "definitionId": defs_id,
        "file": filename,
        "processes": [
            {"id": _attr(p, "id"), "name": _attr(p, "name") or ""} for p in processes
        ],
        "nodes": len(nodes),
        "flows": len(flows),
        "lanes": len(lanes),
        "hasDiagram": bool(has_di),
    }
