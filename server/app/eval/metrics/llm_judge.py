from __future__ import annotations
from typing import Dict, List, Any, Optional
import json
import re
import requests
from app.core.config import settings
from app.core.clients import get_logger
from app.services.gating import _get_process_tasks_from_neo4j

logger = get_logger(__name__)

DEFAULT_JUDGE_MODEL = "atla/selene-mini"


def _ollama_generate(
    prompt: str,
    model: str = DEFAULT_JUDGE_MODEL,
    temperature: float = 0.0,
) -> str:
    """Generiert Antwort via Ollama."""
    try:
        resp = requests.post(
            f"{settings.OLLAMA_BASE}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_ctx": 8192,
                },
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json().get("response", "")
    except Exception as e:
        logger.error(f"Ollama generate Fehler: {e}")
        return ""


def _parse_judge_response(response: str) -> Dict[str, Any]:
    """Parst die Antwort des Judge-Modells."""
    # JSON extrahieren
    json_match = re.search(r"\{[\s\S]*\}", response)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # [[score]] Format
    bracket_match = re.search(r"\[\[(\d+(?:\.\d+)?)\]\]", response)
    if bracket_match:
        return {"score": float(bracket_match.group(1))}

    # Score: X Format
    score_match = re.search(r"[Ss]core[:\s]+(\d+(?:\.\d+)?)", response)
    if score_match:
        return {"score": float(score_match.group(1))}

    return {"score": 0, "parse_error": True}


# ============================================================
# STRUKTUR-FRAGEN (Gating-isoliert)
# ============================================================


def judge_structure_response(
    query: str,
    response: str,
    gating_hint: str,
    allowed_tasks: List[str],
    all_process_tasks: List[str],
    model: str = DEFAULT_JUDGE_MODEL,
) -> Dict[str, Any]:
    """
    Bewertet Antworten auf STRUKTUR-Fragen.

    Diese Fragen können NUR aus dem Gating-Hint beantwortet werden.
    Jede Erwähnung von Tasks außerhalb des Hints ist eine Violation.
    """
    prompt = f"""Du bist ein Evaluator für Prozess-Antworten.

### Aufgabe
Die folgende Frage ist eine STRUKTUR-FRAGE, die nur aus dem Prozesskontext 
(Gating-Hint) beantwortet werden kann - NICHT aus externen Dokumenten.

### Gating-Hint (einzige erlaubte Informationsquelle)
{gating_hint}

### Erlaubte Prozessschritte (aus Gating-Hint)
{json.dumps(allowed_tasks, ensure_ascii=False)}

### Alle Prozessschritte im Prozess (zur Erkennung von Violations)
{json.dumps(all_process_tasks, ensure_ascii=False)}

### Frage
{query}

### Zu bewertende Antwort
{response}

### Bewertungskriterien für STRUKTUR-Fragen
1. Die Antwort darf NUR Schritte aus dem Gating-Hint erwähnen
2. Jeder erwähnte Schritt, der NICHT im Gating-Hint steht, ist eine Violation
3. Erfundene Schritte (nicht in "Alle Prozessschritte") sind schwere Violations

### Bewertungsskala (1-5)
1 = Perfekt: Nur Schritte aus dem Gating-Hint, korrekt und vollständig
2 = Gut: Hauptsächlich korrekt, minimale Abweichungen
3 = Akzeptabel: Einige Schritte außerhalb des Hints, aber keine Erfindungen
4 = Problematisch: Mehrere nicht-erlaubte Schritte oder Vermischung mit externem Wissen
5 = Ungenügend: Ignoriert den Gating-Hint, erfindet Schritte

### Antwortformat (JSON)
{{
    "score": <1-5>,
    "mentioned_from_hint": ["Task1", "Task2"],
    "mentioned_outside_hint": ["Task3"],
    "hallucinated": ["Erfundener Task"],
    "reasoning": "Begründung"
}}"""

    raw_response = _ollama_generate(prompt, model=model)
    result = _parse_judge_response(raw_response)

    score = min(5, max(1, result.get("score", 3)))
    from_hint = result.get("mentioned_from_hint", [])
    outside_hint = result.get("mentioned_outside_hint", [])
    hallucinated = result.get("hallucinated", [])

    total_mentioned = len(from_hint) + len(outside_hint) + len(hallucinated)

    return {
        "score": score,
        "structure_violation_rate": (len(outside_hint) + len(hallucinated))
        / max(1, total_mentioned),
        "hint_adherence": len(from_hint) / max(1, total_mentioned),
        "hallucination_rate": len(hallucinated) / max(1, total_mentioned),
        "mentioned_from_hint": from_hint,
        "mentioned_outside_hint": outside_hint,
        "hallucinated": hallucinated,
        "reasoning": result.get("reasoning", ""),
    }


# ============================================================
# WISSENS-FRAGEN (Retrieval-basiert, mit Gating-Kontext)
# ============================================================


def judge_knowledge_response(
    query: str,
    response: str,
    gating_hint: str,
    retrieved_chunks: List[str],
    allowed_tasks: List[str],
    all_process_tasks: List[str],
    model: str = DEFAULT_JUDGE_MODEL,
) -> Dict[str, Any]:
    """
    Bewertet Antworten auf WISSENS-Fragen.

    Diese Fragen erfordern Dokumentwissen, aber der Gating-Kontext
    sollte respektiert werden (keine Schritte anderer Rollen erwähnen).
    """
    chunks_text = (
        "\n---\n".join(retrieved_chunks[:3]) if retrieved_chunks else "(Keine Chunks)"
    )

    prompt = f"""Du bist ein Evaluator für Prozess-Antworten.

### Aufgabe
Die folgende Frage ist eine WISSENS-FRAGE, die aus Dokumenten beantwortet wird.
Der Gating-Hint gibt den KONTEXT vor - die Antwort sollte diesen respektieren.

### Gating-Hint (Kontextvorgabe)
{gating_hint}

### Relevante Dokument-Chunks
{chunks_text}

### Erlaubte Prozessschritte im aktuellen Kontext
{json.dumps(allowed_tasks, ensure_ascii=False)}

### Alle Prozessschritte im Prozess
{json.dumps(all_process_tasks, ensure_ascii=False)}

### Frage
{query}

### Zu bewertende Antwort
{response}

### Bewertungskriterien für WISSENS-Fragen
1. Die Antwort sollte primär auf den Dokumenten basieren
2. Der Gating-Kontext sollte respektiert werden (fokus auf aktuelle Rolle/Position)
3. Erwähnungen von Schritten anderer Rollen sind akzeptabel, wenn kontextuell begründet
4. Erfundene Informationen sind Violations

### Bewertungsskala (1-5)
1 = Perfekt: Dokument-basiert, Gating-Kontext respektiert
2 = Gut: Hauptsächlich korrekt, Kontext größtenteils respektiert
3 = Akzeptabel: Einige Kontextabweichungen, aber faktisch korrekt
4 = Problematisch: Kontext ignoriert, aber Fakten aus Dokumenten
5 = Ungenügend: Erfundene Informationen oder komplett falscher Kontext

### Antwortformat (JSON)
{{
    "score": <1-5>,
    "document_grounded": true/false,
    "context_respected": true/false,
    "out_of_context_mentions": ["Task1"],
    "reasoning": "Begründung"
}}"""

    raw_response = _ollama_generate(prompt, model=model)
    result = _parse_judge_response(raw_response)

    score = min(5, max(1, result.get("score", 3)))
    out_of_context = result.get("out_of_context_mentions", [])

    return {
        "score": score,
        "knowledge_score": (5 - score) / 4.0,  # Normalisiert: höher = besser
        "document_grounded": result.get("document_grounded", True),
        "context_respected": result.get("context_respected", True),
        "context_violation_count": len(out_of_context),
        "out_of_context_mentions": out_of_context,
        "reasoning": result.get("reasoning", ""),
    }


# ============================================================
# GEMISCHTE FRAGEN (Kombination)
# ============================================================


def judge_mixed_response(
    query: str,
    response: str,
    gating_hint: str,
    retrieved_chunks: List[str],
    allowed_tasks: List[str],
    all_process_tasks: List[str],
    model: str = DEFAULT_JUDGE_MODEL,
) -> Dict[str, Any]:
    """
    Bewertet Antworten auf GEMISCHTE Fragen.

    Kombiniert Struktur- und Wissens-Bewertung.
    """
    chunks_text = (
        "\n---\n".join(retrieved_chunks[:3]) if retrieved_chunks else "(Keine Chunks)"
    )

    prompt = f"""Du bist ein Evaluator für Prozess-Antworten.

### Aufgabe
Die folgende Frage ist eine GEMISCHTE FRAGE, die sowohl Prozesswissen 
als auch Dokumentwissen kombiniert.

### Gating-Hint (Prozesskontext)
{gating_hint}

### Relevante Dokument-Chunks
{chunks_text}

### Erlaubte Prozessschritte im aktuellen Kontext
{json.dumps(allowed_tasks, ensure_ascii=False)}

### Alle Prozessschritte im Prozess
{json.dumps(all_process_tasks, ensure_ascii=False)}

### Frage
{query}

### Zu bewertende Antwort
{response}

### Bewertungskriterien für GEMISCHTE Fragen
Bewerte separat:
A) STRUKTUR: Werden nur erlaubte Prozessschritte erwähnt?
B) WISSEN: Basiert die Antwort auf den Dokumenten?
C) INTEGRATION: Sind Prozess und Dokumente sinnvoll kombiniert?

### Antwortformat (JSON)
{{
    "structure_score": <1-5>,
    "knowledge_score": <1-5>,
    "integration_score": <1-5>,
    "mentioned_tasks_in_scope": ["Task1"],
    "mentioned_tasks_out_of_scope": ["Task2"],
    "hallucinated_tasks": [],
    "document_citations": true/false,
    "reasoning": "Begründung"
}}"""

    raw_response = _ollama_generate(prompt, model=model)
    result = _parse_judge_response(raw_response)

    structure_score = min(5, max(1, result.get("structure_score", 3)))
    knowledge_score = min(5, max(1, result.get("knowledge_score", 3)))
    integration_score = min(5, max(1, result.get("integration_score", 3)))

    in_scope = result.get("mentioned_tasks_in_scope", [])
    out_scope = result.get("mentioned_tasks_out_of_scope", [])
    hallucinated = result.get("hallucinated_tasks", [])

    total = len(in_scope) + len(out_scope) + len(hallucinated)

    return {
        "structure_score": structure_score,
        "knowledge_score": knowledge_score,
        "integration_score": integration_score,
        "combined_score": (structure_score + knowledge_score + integration_score) / 3.0,
        "scope_violation_rate": (len(out_scope) + len(hallucinated)) / max(1, total),
        "hallucination_rate": len(hallucinated) / max(1, total),
        "document_grounded": result.get("document_citations", True),
        "mentioned_tasks_in_scope": in_scope,
        "mentioned_tasks_out_of_scope": out_scope,
        "hallucinated_tasks": hallucinated,
        "reasoning": result.get("reasoning", ""),
    }


# ============================================================
# DISPATCHER: Wählt den richtigen Judge basierend auf Query-Typ
# ============================================================


def h2_judge_by_query_type(
    query: str,
    query_type: str,  # "structure" | "knowledge" | "mixed"
    response: str,
    gating_hint: str,
    retrieved_chunks: List[str],
    expected_gating: Dict[str, Any],
    process_id: Optional[str] = None,
    model: str = DEFAULT_JUDGE_MODEL,
) -> Dict[str, float]:
    """
    Dispatcher: Wählt den passenden Judge basierend auf Query-Typ.
    """

    # Prozessdaten aus Neo4j
    process_data = _get_process_tasks_from_neo4j(process_id) if process_id else {}
    all_task_names = process_data.get("all_task_names", [])
    allowed_tasks = expected_gating.get("expected_task_names", [])

    results: Dict[str, float] = {"query_type": query_type}

    if query_type == "structure":
        # Reine Struktur-Fragen: Strengste Bewertung
        judge_result = judge_structure_response(
            query=query,
            response=response,
            gating_hint=gating_hint,
            allowed_tasks=allowed_tasks,
            all_process_tasks=all_task_names,
            model=model,
        )
        results["h2_structure_violation_rate"] = judge_result[
            "structure_violation_rate"
        ]
        results["h2_hint_adherence"] = judge_result["hint_adherence"]
        results["h2_hallucination_rate"] = judge_result["hallucination_rate"]
        results["h2_score"] = float(judge_result["score"])
        # Hauptmetrik für H2 bei Struktur-Fragen
        results["h2_error_rate"] = judge_result["structure_violation_rate"]

    elif query_type == "knowledge":
        # Wissens-Fragen: Kontext soll respektiert werden
        judge_result = judge_knowledge_response(
            query=query,
            response=response,
            gating_hint=gating_hint,
            retrieved_chunks=retrieved_chunks,
            allowed_tasks=allowed_tasks,
            all_process_tasks=all_task_names,
            model=model,
        )
        results["h2_knowledge_score"] = judge_result["knowledge_score"]
        results["h2_context_respected"] = (
            1.0 if judge_result["context_respected"] else 0.0
        )
        results["h2_context_violation_count"] = float(
            judge_result["context_violation_count"]
        )
        results["h2_score"] = float(judge_result["score"])
        # Hauptmetrik: Context-Violations
        results["h2_error_rate"] = judge_result["context_violation_count"] / max(
            1, len(allowed_tasks)
        )

    else:  # "mixed" oder default
        # Gemischte Fragen: Balancierte Bewertung
        judge_result = judge_mixed_response(
            query=query,
            response=response,
            gating_hint=gating_hint,
            retrieved_chunks=retrieved_chunks,
            allowed_tasks=allowed_tasks,
            all_process_tasks=all_task_names,
            model=model,
        )
        results["h2_structure_score"] = float(judge_result["structure_score"])
        results["h2_knowledge_score"] = float(judge_result["knowledge_score"])
        results["h2_integration_score"] = float(judge_result["integration_score"])
        results["h2_scope_violation_rate"] = judge_result["scope_violation_rate"]
        results["h2_hallucination_rate"] = judge_result["hallucination_rate"]
        # Hauptmetrik: Gewichtete Kombination
        results["h2_error_rate"] = (
            0.5 * judge_result["scope_violation_rate"]
            + 0.3 * judge_result["hallucination_rate"]
            + 0.2 * (1.0 - judge_result.get("document_grounded", 1))
        )

    results["llm_judge_used"] = 1.0
    return results


# ============================================================
# FACTUAL CONSISTENCY (LLM-Judge mit selene-mini)
# ============================================================


def judge_factual_consistency(
    query: str,
    response: str,
    gold_answer: str,
    model: str = DEFAULT_JUDGE_MODEL,  # selene-mini
) -> Dict[str, Any]:
    """
    LLM-basierte Bewertung der faktischen Übereinstimmung.

    Verwendet selene-mini für strukturierte Evaluation.
    Skala: 1-5 (1=perfekt, 5=ungenügend)

    Returns:
        Dict mit score, normalized_score, reasoning
    """
    if not response.strip() or not gold_answer.strip():
        return {
            "factual_consistency_score": 5,
            "factual_consistency_normalized": 0.0,
            "reasoning": "Leere Antwort",
        }

    prompt = f"""Du bist ein Evaluator für Frage-Antwort-Systeme.

### Aufgabe
Bewerte die faktische Übereinstimmung der generierten Antwort mit der Referenz-Antwort.

### Frage
{query}

### Referenz-Antwort (Gold Standard)
{gold_answer}

### Generierte Antwort (zu bewerten)
{response}

### Bewertungskriterien
1. **Faktische Korrektheit**: Stimmen die Fakten überein?
2. **Vollständigkeit**: Werden alle wichtigen Punkte abgedeckt?
3. **Keine Widersprüche**: Widerspricht die Antwort der Referenz?

### Bewertungsskala (1-5)
1 = Perfekt: Faktisch identisch, alle Punkte korrekt
2 = Gut: Überwiegend korrekt, minimale Auslassungen
3 = Akzeptabel: Kernaussagen korrekt, einige Lücken
4 = Problematisch: Wichtige Fakten fehlen oder falsch
5 = Ungenügend: Widerspricht der Referenz oder falsch

### Antwortformat (JSON)
{{
    "score": <1-5>,
    "reasoning": "Kurze Begründung"
}}"""

    raw_response = _ollama_generate(prompt, model=model)
    result = _parse_judge_response(raw_response)

    score = min(5, max(1, result.get("score", 3)))

    return {
        "factual_consistency_score": score,
        "factual_consistency_normalized": (5 - score) / 4.0,  # 0-1, höher = besser
        "reasoning": result.get("reasoning", ""),
    }
