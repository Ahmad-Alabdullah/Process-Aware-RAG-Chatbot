from pydantic import BaseModel, Field
from app.core.config import settings
from typing import List, Literal, Optional


class AskBody(BaseModel):
    # Query + Retrieval
    query: str
    top_k: int = int(settings.TOP_K)

    # HYDE + LLM
    use_hyde: bool = False
    model: str = settings.OLLAMA_MODEL

    # Kontext-Filter
    process_name: Optional[str] = None
    tags: Optional[List[str]] = None
    roles: List[str] = Field(default_factory=list, description="Rollen des Principals")

    # Whitelist-Gating
    whitelist_enabled: bool = Field(
        False, description="Ob Whitelist-Gating aktiviert ist"
    )
    lane_ids: Optional[List[str]] = None
    node_ids: Optional[List[str]] = None
    definition_id: Optional[str] = None
    process_id: Optional[str] = None
    current_node_id: Optional[str] = Field(
        default=None,
        description="Aktueller BPMN-Knoten (xmlId) der Nutzerinteraktion, "
        "z. B. 'Activity_07h9cjl'.",
    )
    prompt_style: Literal["baseline", "no_gating", "fewshot", "cot"] = "baseline"
