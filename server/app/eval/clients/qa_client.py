from __future__ import annotations
import time, httpx
from typing import Dict, Any


class QAClient:
    def __init__(self, base_url: str, timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def ask(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        t0 = time.perf_counter()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(f"{self.base_url}/api/qa/ask", json=payload)
            r.raise_for_status()
            data = r.json()
        data["_latency_ms"] = int((time.perf_counter() - t0) * 1000)
        return data
