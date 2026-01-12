from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.bpmn_store import (
    import_bpmn_xml_and_whitelist,
    list_definitions,
    list_process_nodes_lanes,
    process_graph,
    delete_all_bpmn_data,
    delete_bpmn_by_definition,
)

router = APIRouter(prefix="/api/bpmn")


@router.post(
    "/upload", summary="Upload .bpmn oder .xml (BPMN 2.0) → Neo4j + Auto-Whitelist"
)
async def upload_bpmn(
    file: UploadFile = File(..., description="BPMN 2.0 XML (.bpmn oder .xml)"),
    store_raw: bool = Form(True, description="Roh-XML am Definitionsknoten speichern"),
    auto_whitelist: bool = Form(
        True, description="Whitelist aus Lanes automatisch erzeugen"
    ),
):
    try:
        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="Leere Datei.")
        xml_text = data.decode("utf-8", errors="ignore")

        info = import_bpmn_xml_and_whitelist(
            xml_text=xml_text,
            filename=file.filename or "unnamed.bpmn",
            store_raw=store_raw,
            auto_whitelist=auto_whitelist,
        )
        return {"ok": True, **info}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BPMN-Import fehlgeschlagen: {e}")


from app.services.whitelist import list_whitelist_rules


@router.get(
    "/{definition_id}/whitelist", summary="Whitelist-Regeln anzeigen (per Definition)"
)
def get_whitelist(definition_id: str):
    rules = list_whitelist_rules(definition_id)
    return {
        "ok": True,
        "definitionId": definition_id,
        "rules": rules,
        "count": len(rules),
    }


@router.get("/definitions", summary="Alle BPMN-Definitionen + Prozesse")
def get_definitions():
    return {"ok": True, "definitions": list_definitions()}


@router.get("/processes/{process_id}/combo", summary="Nodes/Lanes für UI-Comboboxen")
def get_process_combo(process_id: str):
    data = list_process_nodes_lanes(process_id)
    if not data:
        raise HTTPException(status_code=404, detail="Prozess nicht gefunden")
    return {"ok": True, **data}


@router.get("/processes/{process_id}/lanes", summary="Lanes für Rollenauswahl")
def get_process_lanes(process_id: str):
    """
    Liefert alle Lanes eines Prozesses für die Rollenauswahl-Combobox.
    
    Returns:
        {
            "ok": true,
            "lanes": [
                {"id": "Lane_1", "name": "Antragsteller", "task_count": 3},
                {"id": "Lane_2", "name": "Vorgesetzter", "task_count": 2}
            ]
        }
    """
    data = list_process_nodes_lanes(process_id)
    if not data:
        raise HTTPException(status_code=404, detail="Prozess nicht gefunden")
    
    lanes = data.get("lanes", [])
    nodes = data.get("nodes", [])
    
    # Only count userTask (manual user tasks, not automated system tasks)
    user_facing_types = {"userTask"}
    
    # Count tasks per lane (only actual tasks, not events/gateways)
    lane_task_counts = {}
    for node in nodes:
        if node.get("type") not in user_facing_types:
            continue
        lane_id = node.get("laneId")
        if lane_id:
            lane_task_counts[lane_id] = lane_task_counts.get(lane_id, 0) + 1
    
    # Format for combobox - exclude lanes with 0 tasks
    formatted_lanes = [
        {
            "id": lane["id"],
            "name": lane["name"],
            "task_count": lane_task_counts.get(lane["id"], 0)
        }
        for lane in lanes
        if lane.get("id") and lane_task_counts.get(lane["id"], 0) > 0
    ]
    
    return {"ok": True, "lanes": formatted_lanes}


@router.get("/processes/{process_id}/graph", summary="Prozessgraph (Nodes + Edges)")
def get_process_graph(process_id: str):
    g = process_graph(process_id)
    return {"ok": True, **g}


@router.delete(
    "/all",
    summary="Alle BPMN-Daten löschen (Definitions, Processes, Nodes, Lanes, Whitelists)",
)
def delete_all_bpmn():
    """
    Löscht ALLE BPMN-Daten aus Neo4j:
    - BPMN Definitions
    - Processes
    - Nodes
    - Lanes
    - Whitelists + WhitelistRules
    - Participants
    """
    result = delete_all_bpmn_data()
    return {"ok": True, **result}


@router.delete(
    "/definitions/{definition_id}",
    summary="Eine BPMN-Definition mit allen zugehörigen Daten löschen",
)
def delete_definition(definition_id: str):
    """
    Löscht eine spezifische BPMN-Definition und alle zugehörigen Daten:
    - Die Definition selbst
    - Alle Processes der Definition
    - Alle Nodes der Processes
    - Alle Lanes der Processes
    - Whitelist + WhitelistRules der Definition
    """
    if not definition_id:
        raise HTTPException(
            status_code=400, detail="definition_id darf nicht leer sein"
        )

    result = delete_bpmn_by_definition(definition_id)

    if result.get("found") is False:
        raise HTTPException(
            status_code=404, detail=f"Definition '{definition_id}' nicht gefunden"
        )

    return {"ok": True, **result}
