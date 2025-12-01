from __future__ import annotations
from typing import Dict, Any
from pydantic import BaseModel, Field


class RunConfig(BaseModel):
    run_name: str
    dataset: str
    qa_base_url: str
    qa_payload: Dict[str, Any] = Field(default_factory=dict)
    factors: Dict[str, Any] = Field(default_factory=dict)
    logging: Dict[str, Any] = Field(default_factory=dict)
    ranking_sources: list[str] = Field(
        default_factory=lambda: ["rrf", "ce"],
        description="Reihenfolge der bevorzugten retrieval_logs.source beim Scoring",
    )
    ranking_fallback_all: bool = Field(
        default=True,
        description="Falls keine Einträge mit ranking_sources gefunden werden, alle Quellen verwenden.",
    )
