from pydantic import BaseModel, Field
from typing import List, Optional
from app.core.config import settings


class AskBody(BaseModel):
    # Query + Retrieval
    query: str
    top_k: int = int(settings.TOP_K)

    # Reranking (Cross-Encoder)
    use_rerank: bool = Field(
        default=False,
        description="Cross-Encoder Reranking aktivieren (Jina Reranker v3)",
    )
    rerank_top_n: int = Field(
        default=50,
        description="Anzahl Kandidaten für Reranking vor finale Top-K Auswahl",
    )

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
    definition_id: Optional[str] = Field(default=None, description="BPMN Definition-ID")
    current_node_id: Optional[str] = Field(
        default=None,
        description="Aktuelle Node-ID im BPMN für lokalen Kontext (aktiviert GATING_ENABLED)",
    )

    # Ablation-Study: Grober Prozesskontext ohne Lokalisierung
    force_process_context: bool = Field(
        default=False,
        description="Erzwingt PROCESS_CONTEXT Modus (nur für Ablation-Study)",
    )

    # Prompt-Konfiguration
    prompt_style: str = Field(default="baseline", description="Prompt-Style")

    # Debug
    debug_return: bool = Field(
        default=False, description="Debug-Informationen zurückgeben"
    )
