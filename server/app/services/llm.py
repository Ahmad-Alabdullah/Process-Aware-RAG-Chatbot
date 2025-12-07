import requests
from app.core.config import settings
from llama_index.core.indices.query.query_transform.base import HyDEQueryTransform


def ollama_generate(prompt: str, model: str = "llama3.1:8b") -> str:
    resp = requests.post(
        f"{settings.OLLAMA_BASE}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_ctx": 8191},
        },
    )
    resp.raise_for_status()
    return resp.json().get("response", "")


def hyde_rewrite(query: str, model: str = "llama3.1:8b") -> str:
    """
    HyDE über LlamaIndex (neue Importpfade). Falls nicht erwünscht, gib einfach query zurück.
    """
    try:
        hyde = HyDEQueryTransform(llm=None)
        return query
    except Exception:
        return query
