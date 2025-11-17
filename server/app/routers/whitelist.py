from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from app.services.whitelist import (
    WhitelistSpec,
    allowed_for_principal,
    upsert_whitelist,
    next_allowed,
)

router = APIRouter(prefix="/api/policy")


class WhitelistIn(BaseModel):
    id: str = Field(..., description="Technische ID, z.B. wl_car_01")
    name: str
    process_id: str
    allow_nodes: List[str] = []
    allow_lanes: List[str] = []
    allow_types: List[str] = []
    principals: List[str] = []


class AllowedForPrincipalOut(BaseModel):
    definition_id: str
    roles: List[str]
    node_ids: List[str]
    lane_ids: List[str]


@router.post("/whitelists", summary="Create/replace a whitelist")
def create_whitelist(body: WhitelistIn):
    try:
        spec = WhitelistSpec(**body.model_dump())
        res = upsert_whitelist(spec)
        return {"ok": True, "whitelist": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"whitelist upsert failed: {e}")


class NextAllowedIn(BaseModel):
    process_id: str
    current_node_id: str
    whitelist_ids: List[str] = []
    max_depth: int = 1


@router.post(
    "/whitelists/next", summary="Compute next allowed nodes from current position"
)
def compute_next_allowed(body: NextAllowedIn):
    wids = list(body.whitelist_ids)
    if not wids:
        return {"ok": True, "next": []}
    try:
        rows = next_allowed(body.process_id, body.current_node_id, wids, body.max_depth)
        return {"ok": True, "next": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"next-allowed failed: {e}")


@router.get(
    "/definitions/{definition_id}/allowed",
    response_model=AllowedForPrincipalOut,
    summary="Aggregierte erlaubte Nodes/Lanes für Principal/Rollen (UI-Overlay)",
)
def get_allowed_for_principal(
    definition_id: str,
    roles: Optional[str] = None,
):
    role_list = [r.strip() for r in (roles or "").split(",") if r.strip()]
    res = allowed_for_principal(definition_id, role_list)
    return AllowedForPrincipalOut(
        definition_id=definition_id,
        roles=role_list,
        node_ids=res["nodeIds"],
        lane_ids=res["laneIds"],
    )
