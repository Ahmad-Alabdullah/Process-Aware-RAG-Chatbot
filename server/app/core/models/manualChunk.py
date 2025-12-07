from fastapi import Form
from pydantic import BaseModel
from typing import Dict, Any, Literal, Optional


class ManualChunk(BaseModel):
    document_id: str
    text: str
    meta: Dict[str, Any] = {}
    process_name: Optional[str] = None
    tags: Optional[str] = None
    chunking_strategy: Literal["by_title", "semantic"] = None
