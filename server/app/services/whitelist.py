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
        s.run(
            """CREATE CONSTRAINT principal_id_unique IF NOT EXISTS
                 FOR (p:Principal) REQUIRE p.id IS UNIQUE"""
        )


# ---------- Upsert Whitelist ----------
def upsert_whitelist(spec: WhitelistSpec) -> Dict[str, Any]:
    spec = spec.normalized()
    ensure_schema()
    with _driver().session() as s:
        # Whitelist-Knoten
        s.run(
            """
        MERGE (w:Whitelist {id:$id})
          ON CREATE SET w.name=$name, w.processId=$pid, w.allow_types=$atypes
          ON MATCH  SET w.name=$name, w.processId=$pid, w.allow_types=$atypes
        """,
            id=spec.id,
            name=spec.name,
            pid=spec.process_id,
            atypes=spec.allow_types,
        )

        # Beziehungen zu Nodes
        s.run(
            """
        MATCH (w:Whitelist {id:$id})
        OPTIONAL MATCH (w)-[r:ALLOWS_NODE]->(:Node)
        DELETE r
        WITH w
        UNWIND $nids AS nid
        MATCH (n:Node {id:nid, processId:$pid})
        MERGE (w)-[:ALLOWS_NODE]->(n)
        """,
            id=spec.id,
            pid=spec.process_id,
            nids=spec.allow_nodes,
        )

        # Beziehungen zu Lanes
        s.run(
            """
        MATCH (w:Whitelist {id:$id})
        OPTIONAL MATCH (w)-[r:ALLOWS_LANE]->(:Lane)
        DELETE r
        WITH w
        UNWIND $lids AS lid
        MATCH (l:Lane {id:lid, processId:$pid})
        MERGE (w)-[:ALLOWS_LANE]->(l)
        """,
            id=spec.id,
            pid=spec.process_id,
            lids=spec.allow_lanes,
        )

        # Principals binden
        s.run(
            """
        MATCH (w:Whitelist {id:$id})
        OPTIONAL MATCH (:Principal)-[r:USES]->(w)
        DELETE r
        WITH w
        UNWIND $pids AS pid
        MERGE (p:Principal {id:pid})
        MERGE (p)-[:USES]->(w)
        """,
            id=spec.id,
            pids=spec.principals,
        )

        rec = s.run(
            """
        MATCH (w:Whitelist {id:$id})
        OPTIONAL MATCH (w)-[:ALLOWS_NODE]->(n:Node {processId:w.processId})
        WITH w, collect(n.id) AS nids
        OPTIONAL MATCH (w)-[:ALLOWS_LANE]->(l:Lane {processId:w.processId})
        RETURN w.id AS id, w.name AS name, w.processId AS processId, nids AS allow_nodes,
               collect(l.id) AS allow_lanes, w.allow_types AS allow_types
        """,
            id=spec.id,
        ).single()
        return dict(rec) if rec else {"ok": False}


# ---------- Resolve principal -> whitelist ids ----------
def whitelists_for_principal(principal_id: str) -> List[str]:
    with _driver().session() as s:
        rows = s.run(
            """
        MATCH (p:Principal {id:$pid})-[:USES]->(w:Whitelist)
        RETURN w.id AS id
        """,
            pid=principal_id,
        ).values()
        return [r[0] for r in rows]


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
