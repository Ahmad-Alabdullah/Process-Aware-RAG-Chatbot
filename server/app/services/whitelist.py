from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from neo4j import GraphDatabase
from app.core.config import settings


# ---------- Neo4j Driver ----------
def _driver():
    return GraphDatabase.driver(
        settings.NEO4J_URL,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
    )


# ---------- Datamodel ----------
@dataclass
class WhitelistSpec:
    id: str
    name: str
    process_id: str
    allow_nodes: List[str] = None
    allow_lanes: List[str] = None
    allow_types: List[str] = None  # z.B. ["userTask","serviceTask"]
    principals: List[str] = None  # optionale Bindung (Rollen/Benutzer)

    def normalized(self):
        return WhitelistSpec(
            id=self.id,
            name=self.name,
            process_id=self.process_id,
            allow_nodes=self.allow_nodes or [],
            allow_lanes=self.allow_lanes or [],
            allow_types=[t for t in (self.allow_types or [])],
            principals=self.principals or [],
        )


# ---------- Schema / Constraints ----------
def ensure_schema():
    with _driver().session() as s:
        s.run(
            """CREATE CONSTRAINT whitelist_id_unique IF NOT EXISTS
                 FOR (w:Whitelist) REQUIRE w.id IS UNIQUE"""
        )


# ---------- Upsert Whitelist ----------
def upsert_whitelist(spec: WhitelistSpec) -> dict:
    ensure_schema()
    with _driver().session() as s:
        s.run(
            """
        MERGE (w:Whitelist {id:$id})
        SET w.name=$name, w.processId=$process_id
        """,
            **spec.model_dump(),
        )

        # Bind Whitelist zu Process
        s.run(
            """
        MATCH (pr:Process {xmlId:$pid})
        MATCH (w:Whitelist {id:$wid})
        MERGE (w)-[:FOR_PROCESS]->(pr)
        """,
            pid=spec.process_id,
            wid=spec.id,
        )

        # Erlaubte Nodes (xmlId)
        s.run(
            """
        UNWIND $nids AS nid
        MATCH (n:Node {xmlId:nid})
        MATCH (w:Whitelist {id:$wid})
        MERGE (w)-[:ALLOW_NODE]->(n)
        """,
            nids=spec.allow_nodes,
            wid=spec.id,
        )

        # Erlaubte Lanes (xmlId)
        s.run(
            """
        UNWIND $lids AS lid
        MATCH (l:Lane {xmlId:lid})
        MATCH (w:Whitelist {id:$wid})
        MERGE (w)-[:ALLOW_LANE]->(l)
        """,
            lids=spec.allow_lanes,
            wid=spec.id,
        )

        # Erlaubte Typen
        s.run(
            """
        MATCH (w:Whitelist {id:$wid})
        SET w.allowTypes = $types
        """,
            wid=spec.id,
            types=spec.allow_types,
        )

        # Principals ↔ Whitelist
        s.run(
            """
        UNWIND $p AS pid
        MERGE (u:Principal {id:pid})
        WITH u
        MATCH (w:Whitelist {id:$wid})
        MERGE (u)-[:USES]->(w)
        """,
            p=spec.principals,
            wid=spec.id,
        )

        return {"id": spec.id}


# ---------- Allowed Node IDs for a whitelist ----------
def _allowed_node_ids(
    wid: str, process_id: str
) -> Tuple[List[str], List[str], List[str]]:
    with _driver().session() as s:
        rec = s.run(
            """
        MATCH (w:Whitelist {id:$wid, processId:$pid})
        OPTIONAL MATCH (w)-[:ALLOWS_NODE]->(n:Node {processId:$pid})
        WITH w, collect(n.id) AS direct
        OPTIONAL MATCH (w)-[:ALLOWS_LANE]->(l:Lane {processId:$pid})-[:CONTAINS]->(m:Node {processId:$pid})
        WITH w, direct, collect(DISTINCT m.id) AS via_lanes
        RETURN w.allow_types AS allow_types, direct, via_lanes
        """,
            wid=wid,
            pid=process_id,
        ).single()
        if not rec:
            return [], [], []
        return rec["allow_types"] or [], rec["direct"] or [], rec["via_lanes"] or []


def allowed_nodes_union(wids: List[str], process_id: str) -> Tuple[Set[str], Set[str]]:
    """Union über mehrere Whitelists -> (nodeIds, allowedTypes)."""
    node_ids: Set[str] = set()
    types: Set[str] = set()
    for wid in wids:
        atypes, direct, via = _allowed_node_ids(wid, process_id)
        node_ids.update(direct)
        node_ids.update(via)
        types.update(atypes)
    return node_ids, types


# ---------- Next allowed nodes (path search + filter) ----------
def next_allowed(
    process_id: str, current_node_id: str, wids: List[str], max_depth: int = 1
) -> List[Dict[str, Any]]:
    """Pfadsuche n->m mit 1..max_depth, m in erlaubten Nodes und (optional) Typfilter."""
    allow_node_ids, allow_types = allowed_nodes_union(wids, process_id)
    if not allow_node_ids:
        return []
    with _driver().session() as s:
        rows = s.run(
            """
        MATCH (n:Node {id:$nid, processId:$pid})
        MATCH path=(n)-[:FLOWS_TO*1..$d]->(m:Node {processId:$pid})
        WHERE m.id IN $allowed
        RETURN m.id AS id, m.name AS name, m.type AS type, length(path) AS hops
        ORDER BY hops ASC, name ASC
        """,
            nid=current_node_id,
            pid=process_id,
            d=max_depth,
            allowed=list(allow_node_ids),
        ).data()
        if allow_types:
            rows = [r for r in rows if r["type"] in allow_types]
        return rows


# ---------- Filters for Retrieval ----------
def build_os_filter(
    process_id: str, node_ids: List[str] = None, lane_ids: List[str] = None
) -> Dict[str, Any]:
    """
    OpenSearch Filter-DSL: bool.filter, z.B. nach meta.processId / meta.nodeId / meta.laneId
    """
    filt: List[Dict[str, Any]] = [{"term": {"meta.processId": process_id}}]
    if node_ids:
        filt.append({"terms": {"meta.nodeId": node_ids}})
    if lane_ids:
        filt.append({"terms": {"meta.laneId": lane_ids}})
    return {"bool": {"filter": filt}}


def build_qdrant_filter(
    process_id: str, node_ids: List[str] = None, lane_ids: List[str] = None
) -> Dict[str, Any]:
    """
    Qdrant Filter (client-agnostic dict): 'must' von FieldConditions.
    """
    must = [{"key": "processId", "match": {"value": process_id}}]
    if node_ids:
        # entweder viele "should" mit at_least=1, oder "match" über 'any' (je nach Client)
        must.append({"key": "nodeId", "match": {"any": node_ids}})
    if lane_ids:
        must.append({"key": "laneId", "match": {"any": lane_ids}})
    return {"must": must}


def create_default_whitelist(definition_id: str) -> Dict[str, int]:
    """
    Erzeugt je Lane eine Whitelist-Regel:
      - allowedRoles = [Lane.name]   (Best Practice: Lanes nach Rollen/Funktionen benennen)
      - nodeIds = alle flowNodeRef der Lane
      - processId = zugehöriger Prozess
    Falls keine Lanes vorhanden sind: 1 Regel je Prozess (alle Nodes).
    """
    rules_created = 0
    lanes_count = 0

    with _driver().session() as s:
        # Whitelist-Knoten je Definition
        s.run(
            """
        MERGE (w:Whitelist {definitionId:$defs})
        ON CREATE SET w.createdAt=timestamp()
        """,
            defs=definition_id,
        )

        # Lanes + Node-Mapping + Prozess
        data = s.run(
            """
        MATCH (d:BPMN {definitionId:$defs})-[:CONTAINS]->(pr:Process)-[:HAS_LANE]->(l:Lane)
        OPTIONAL MATCH (l)-[:CONTAINS]->(n:Node)
        WITH d, pr, l, collect(n.xmlId) AS nodeIds
        RETURN pr.xmlId AS processId, l.xmlId AS laneId, coalesce(l.name,'') AS laneName, nodeIds
        """,
            defs=definition_id,
        ).data()

        if data:
            lanes_count = len({row["laneId"] for row in data})
            for row in data:
                process_id = row["processId"]
                lane_id = row["laneId"]
                lane_name = row["laneName"]
                node_ids = [nid for nid in row["nodeIds"] if nid]
                s.run(
                    """
                MATCH (w:Whitelist {definitionId:$defs})
                MERGE (r:WhitelistRule {definitionId:$defs, laneId:$laneId})
                SET r.processId=$proc, r.nodeIds=$nodes,
                    r.allowedRoles = CASE WHEN $laneName='' THEN [] ELSE [$laneName] END,
                    r.allowedPrincipals = coalesce(r.allowedPrincipals, [])
                MERGE (w)-[:HAS_RULE]->(r)
                """,
                    defs=definition_id,
                    laneId=lane_id,
                    proc=process_id,
                    nodes=node_ids,
                    laneName=lane_name,
                )
                rules_created += 1
        else:
            # Fallback: Keine Lanes → Regeln je Prozess mit allen Nodes
            data2 = s.run(
                """
            MATCH (d:BPMN {definitionId:$defs})-[:CONTAINS]->(pr:Process)-[:CONTAINS]->(n:Node)
            WITH pr, collect(DISTINCT n.xmlId) AS nodes
            RETURN pr.xmlId AS processId, nodes
            """,
                defs=definition_id,
            ).data()
            for row in data2:
                s.run(
                    """
                MATCH (w:Whitelist {definitionId:$defs})
                MERGE (r:WhitelistRule {definitionId:$defs, processId:$proc, laneId:'*'})
                SET r.nodeIds=$nodes,
                    r.allowedRoles = coalesce(r.allowedRoles, []),
                    r.allowedPrincipals = coalesce(r.allowedPrincipals, [])
                MERGE (w)-[:HAS_RULE]->(r)
                """,
                    defs=definition_id,
                    proc=row["processId"],
                    nodes=row["nodes"],
                )
                rules_created += 1

    return {"rules": rules_created, "lanes": lanes_count}


def list_whitelist_rules(definition_id: str) -> List[Dict]:
    with _driver().session() as s:
        rows = s.run(
            """
        MATCH (w:Whitelist {definitionId:$defs})-[:HAS_RULE]->(r:WhitelistRule)
        RETURN r.definitionId AS definitionId, r.processId AS processId, r.laneId AS laneId,
               r.allowedRoles AS allowedRoles, r.allowedPrincipals AS allowedPrincipals,
               r.nodeIds AS nodeIds
        ORDER BY r.processId, r.laneId
        """,
            defs=definition_id,
        ).data()
    return rows


def allowed_for_principal(
    definition_id: str,
    roles: List[str] | None = None,
) -> Dict[str, List[str]]:
    """
    Aggregiert erlaubte Lane- und Node-IDs ausschließlich rollenbasiert.
    """
    roles = roles or []
    if not roles:
        return {"nodeIds": [], "laneIds": []}

    with _driver().session() as s:
        rows = s.run(
            """
            MATCH (w:Whitelist {definitionId:$defs})-[:HAS_RULE]->(r:WhitelistRule)
            WHERE size($roles) > 0 AND any(x IN $roles WHERE x IN r.allowedRoles)
            RETURN collect(DISTINCT r.laneId) AS lanes,
                   reduce(acc = [], n IN r.nodeIds | acc + n) AS nodes
            """,
            defs=definition_id,
            roles=roles,
        ).data()

    if not rows:
        return {"nodeIds": [], "laneIds": []}

    lanes = [l for l in (rows[0]["lanes"] or []) if l]
    nodes = [n for n in (rows[0]["nodes"] or []) if n]

    return {
        "nodeIds": sorted(set(nodes)),
        "laneIds": sorted(set(lanes)),
    }
