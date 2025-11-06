from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from app.services.whitelist import (
    WhitelistSpec,
    upsert_whitelist,
    whitelists_for_principal,
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


@router.post("/whitelists", summary="Create/replace a whitelist")
def create_whitelist(body: WhitelistIn):
    try:
        spec = WhitelistSpec(**body.model_dump())
        res = upsert_whitelist(spec)
        return {"ok": True, "whitelist": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"whitelist upsert failed: {e}")


@router.get(
    "/principals/{principal_id}/whitelists",
    summary="List whitelist IDs bound to a principal",
)
def list_whitelists_for_principal(principal_id: str):
    return {
        "principal": principal_id,
        "whitelists": whitelists_for_principal(principal_id),
    }


class NextAllowedIn(BaseModel):
    process_id: str
    current_node_id: str
    principal_id: Optional[str] = None
    whitelist_ids: List[str] = []
    max_depth: int = 1


@router.post(
    "/whitelists/next", summary="Compute next allowed nodes from current position"
)
def compute_next_allowed(body: NextAllowedIn):
    wids = list(body.whitelist_ids)
    if body.principal_id:
        wids.extend(whitelists_for_principal(body.principal_id))
    if not wids:
        return {"ok": True, "next": []}
    try:
        rows = next_allowed(body.process_id, body.current_node_id, wids, body.max_depth)
        return {"ok": True, "next": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"next-allowed failed: {e}")
