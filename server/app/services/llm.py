"""
LLM-Service mit konfigurierbaren Generierungsparametern.

Verwendet LLMConfig für konsistente Parameter über alle Use Cases.
"""

import requests
from typing import Optional
from app.core.config import settings
from app.core.llm_config import LLMConfig, LLMPresets
from app.core.prompt_builder import extract_answer_from_cot


def ollama_generate(
    prompt: str,
    config: Optional[LLMConfig] = None,
) -> str:
    """
    Generiert Antwort via Ollama.

    Args:
        prompt: Der Prompt
        config: LLMConfig mit allen Parametern

    Returns:
        Generierte Antwort als String
    """
    # Default-Config falls nicht angegeben
    if config is None:
        config = LLMPresets.rag_qa(settings.OLLAMA_MODEL)

    # Ollama-Request
    options = {
        "num_ctx": config.num_ctx,
        "temperature": config.temperature,
        "num_predict": config.max_tokens,
        "repeat_penalty": config.repeat_penalty,
    }

    # Optionale Parameter
    if config.top_p is not None:
        options["top_p"] = config.top_p
    if config.top_k is not None:
        options["top_k"] = config.top_k

    resp = requests.post(
        f"{settings.OLLAMA_BASE}/api/generate",
        json={
            "model": config.model,
            "prompt": prompt,
            "stream": False,
            "options": options,
        },
        timeout=120,
    )
    resp.raise_for_status()
    response = resp.json().get("response", "")

    # CoT-Postprocessing: Entferne <think>-Tags
    if "<think>" in response:
        response = extract_answer_from_cot(response)

    return response.strip()


def hyde_rewrite(query: str, model: Optional[str] = None) -> str:
    """
    HyDE: Hypothetical Document Embeddings.

    Generiert ein hypothetisches Dokument für besseres Retrieval.
    Verwendet höheres Temperature (0.3) für Variabilität.
    """
    config = LLMPresets.hyde(model=model or settings.OLLAMA_MODEL)

    prompt = f"""Schreibe einen kurzen Absatz (2-3 Sätze), der die folgende Frage beantwortet.
Der Text soll wie ein Ausschnitt aus einem Hochschul-Verwaltungsdokument klingen.

Frage: {query}

Hypothetisches Dokument:"""

    return ollama_generate(prompt, config=config)


def generate_for_evaluation(
    prompt: str,
    model: str = "atla/selene-mini",
) -> str:
    """
    Generierung für LLM-Judge Evaluation.

    Verwendet Temperature=0.0 für Reproduzierbarkeit.
    """
    config = LLMPresets.evaluation(model=model)
    return ollama_generate(prompt, config=config)
