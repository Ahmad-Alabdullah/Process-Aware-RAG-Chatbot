from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.bpmn_store import import_bpmn_xml_and_whitelist

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
