from pydantic import BaseModel, Field
from typing import List, Optional
from app.core.config import settings


class AskBody(BaseModel):
    # Query + Retrieval
    query: str
    top_k: int = int(settings.TOP_K)

    # HYDE + LLM
    use_hyde: bool = False
    model: str = settings.OLLAMA_MODEL

    # Kontext-Filter (für Retrieval)
    process_name: Optional[str] = Field(
        default=None, description="Prozessname als Filter/Boost für Retrieval"
    )
    tags: Optional[List[str]] = None

    # Rollen (für Whitelist-Gating bei GATING_ENABLED)
    roles: List[str] = Field(
        default_factory=list, description="Rollen des Nutzers für Whitelist-Filter"
    )

    # Prozess-Kontext (aktiviert GATING_ENABLED wenn current_node_id gesetzt)
    process_id: Optional[str] = Field(
        default=None, description="BPMN Process-ID (xmlId)"
    )
    definition_id: Optional[str] = Field(
        default=None, description="BPMN Definition-ID für Whitelist-Lookup"
    )
    current_node_id: Optional[str] = Field(
        default=None,
        description="Aktueller BPMN-Knoten (xmlId) - aktiviert lokales Gating",
    )

    # Ablation-Study: Erzwingt PROCESS_CONTEXT Modus
    force_process_context: bool = Field(
        default=False,
        description="Nur für Ablation: Erzwingt groben Prozesskontext ohne lokale Position",
    )

    # Prompt-Stil
    prompt_style: str = Field(
        default="baseline", description="Prompt-Stil: baseline, fewshot, cot"
    )
