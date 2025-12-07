from __future__ import annotations
from typing import Dict, Any, Optional
import httpx


class QAClient:
    def __init__(self, base_url: str, timeout: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def ask(
        self, payload: Dict[str, Any], query_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Sendet eine Frage an den QA-Endpoint.

        Args:
            payload: Request Body
            query_params: Optionale Query-Parameter (für Embedding-Config)
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Query-Parameter filtern (nur non-None)
            params = {}
            if query_params:
                params = {k: v for k, v in query_params.items() if v is not None}

            resp = await client.post(
                f"{self.base_url}/api/qa/ask",
                json=payload,
                params=params if params else None,
            )
            resp.raise_for_status()
            return resp.json()
