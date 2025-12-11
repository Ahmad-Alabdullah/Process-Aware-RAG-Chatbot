from __future__ import annotations
from typing import Dict, List, Any, Optional
import json
import re
import requests
from app.core.config import settings
from app.core.clients import get_logger
from app.services.gating import _get_process_tasks_from_neo4j
from app.core.llm_config import LLMPresets

logger = get_logger(__name__)

DEFAULT_JUDGE_MODEL = "atla/selene-mini"


def _ollama_generate_judge(
    prompt: str,
    model: str = DEFAULT_JUDGE_MODEL,
) -> str:
    """
    Generiert Antwort via Ollama für Evaluation.

    WICHTIG: Temperature=0.0 für Reproduzierbarkeit!

    Wissenschaftliche Begründung:
    - Evaluationsmetriken müssen reproduzierbar sein
    - Verschiedene Runs sollten gleiche Scores liefern
    - Temperature=0 eliminiert Sampling-Varianz
    """
    config = LLMPresets.evaluation(model=model)

    try:
        resp = requests.post(
            f"{settings.OLLAMA_BASE}/api/generate",
            json={
                "model": config.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": config.temperature,  # 0.0
                    "num_ctx": config.num_ctx,
                    "num_predict": config.max_tokens,
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
    """Parst die JSON-Antwort des Judge-Modells."""
    # ... existing parsing logic ...
    try:
        # Versuche JSON zu extrahieren
        json_match = re.search(r"\{[^{}]*\}", response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except json.JSONDecodeError:
        pass

    return {"error": "Could not parse response", "raw": response}


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

    raw_response = _ollama_generate_judge(prompt, model=model)
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

    raw_response = _ollama_generate_judge(prompt, model=model)
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

    raw_response = _ollama_generate_judge(prompt, model=model)
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
# RAG TRIAD METRICS (RAGAS-Style, Reference-Free)
# ============================================================


def judge_answer_relevance(
    query: str,
    response: str,
    model: str = DEFAULT_JUDGE_MODEL,
) -> Dict[str, Any]:
    """
    Bewertet: Beantwortet die Antwort die Frage? (Answer Relevance)
    Strategie: Bewertet direkt, ob die Antwort eine sinnvolle Reaktion auf die Frage ist.
    """
    prompt = f"""Du bist ein Evaluator für QA-Systeme.

### Aufgabe
Bewerte die Relevanz der Antwort auf die gegebene Frage.
Ignoriere, ob die Antwort faktisch wahr ist (das prüft ein anderer Schritt).
Prüfe nur: Adressiert diese Antwort direkt das Anliegen der Frage?

### Frage
{query}

### Antwort
{response}

### Bewertungskriterien
1. Adressiert die Antwort den Kern der Frage?
2. Ist die Antwort spezifisch oder nur eine allgemeine Floskel?
3. "Ich weiß nicht" ist relevant, wenn keine Infos vorhanden sind.

### Bewertungsskala (1-5)
5 = Perfekt: Präzise, direkte Antwort auf die Frage
4 = Gut: Beantwortet die Frage, vielleicht etwas weitschweifig
3 = Akzeptabel: Thema getroffen, aber vage oder indirekt
2 = Schwach: Thema nur gestreift, Frage nicht wirklich beantwortet
1 = Irrelevant: Antwort hat nichts mit der Frage zu tun

### Antwortformat (JSON)
{{
    "score": <1-5>,
    "reasoning": "Kurze Begründung"
}}"""

    raw = _ollama_generate_judge(prompt, model=model)
    parsed = _parse_judge_response(raw)
    score = min(5, max(1, parsed.get("score", 3)))
    
    return {
        "answer_relevance_score": score,
        "answer_relevance_normalized": (score - 1) / 4.0,
        "reasoning": parsed.get("reasoning", "")
    }


def judge_context_relevance(
    query: str,
    chunks: List[str],
    model: str = DEFAULT_JUDGE_MODEL,
) -> Dict[str, Any]:
    """
    Bewertet: Sind die abgerufenen Chunks hilfreich? (Context Relevance)
    """
    context_text = "\n---\n".join(chunks[:5]) if chunks else "(Kein Kontext)"
    
    prompt = f"""Du bist ein Evaluator für Retrieval-Systeme.

### Aufgabe
Bewerte, ob die abgerufenen Text-Chunks nützliche Informationen enthalten, 
um die Frage zu beantworten. Ignoriere, ob die Antwort korrekt ist.

### Frage
{query}

### Abgerufene Chunks (Kontext)
{context_text}

### Bewertungsskala (1-5)
5 = Perfekt: Chunks enthalten die exakte Antwort und wichtige Details
4 = Gut: Chunks enthalten die Antwort, aber auch Rauschen
3 = Akzeptabel: Chunks sind thematisch relevant, Antwort ableitbar
2 = Schwach: Nur lose verwandte Keywords, Antwort kaum möglich
1 = Nutzlos: Chunks haben nichts mit der Frage zu tun

### Antwortformat (JSON)
{{
    "score": <1-5>,
    "reasoning": "Kurze Begründung"
}}"""

    raw = _ollama_generate_judge(prompt, model=model)
    parsed = _parse_judge_response(raw)
    score = min(5, max(1, parsed.get("score", 3)))

    return {
        "context_relevance_score": score,
        "context_relevance_normalized": (score - 1) / 4.0,
        "reasoning": parsed.get("reasoning", "")
    }


def judge_faithfulness(
    response: str,
    chunks: List[str],
    model: str = DEFAULT_JUDGE_MODEL,
) -> Dict[str, Any]:
    """
    Bewertet: Stammt die Antwort NUR aus dem Kontext? (Faithfulness/Groundedness)
    Prüft auf Halluzinationen.
    """
    context_text = "\n---\n".join(chunks[:5]) if chunks else "(Kein Kontext)"
    
    prompt = f"""Du bist ein Evaluator für Halluzinationen.

### Aufgabe
Prüfe, ob JEDE Aussage in der Antwort durch den gegebenen Kontext belegt ist.
Nutze KEIN eigenes Wissen. Wenn eine Aussage nicht im Kontext steht, ist es eine Halluzination.

### Kontext
{context_text}

### Antwort
{response}

### Bewertungsskala (1-5)
5 = Perfekt: Jeder Satz ist eindeutig durch den Kontext belegt
4 = Gut: Fast alles belegt, minimale, triviale Ergänzungen
3 = Akzeptabel: Hauptaussagen belegt, aber einige Details nicht im Kontext
2 = Bedenklich: Enthält wesentliche Infos, die nicht im Kontext stehen
1 = Halluzination: Antwort hat wenig bis nichts mit dem Kontext zu tun

### Antwortformat (JSON)
{{
    "score": <1-5>,
    "hallucinated_statements": ["Aussage 1", "Aussage 2"],
    "reasoning": "Begründung"
}}"""

    raw = _ollama_generate_judge(prompt, model=model)
    parsed = _parse_judge_response(raw)
    score = min(5, max(1, parsed.get("score", 3)))

    return {
        "faithfulness_score": score,
        "faithfulness_normalized": (score - 1) / 4.0,
        "hallucinated_statements": parsed.get("hallucinated_statements", []),
        "reasoning": parsed.get("reasoning", "")
    }


# ============================================================
# FACTUAL CONSISTENCY (Reference-Based)


def judge_factual_consistency(
    query: str,
    response: str,
    gold_answer: str,
    model: str = DEFAULT_JUDGE_MODEL,
) -> Dict[str, Any]:
    """
    Bewertet faktische Konsistenz der Antwort.

    Temperature=0.0 (via LLMPresets.evaluation) für Reproduzierbarkeit.

    Returns:
        Dict mit:
        - factual_consistency_score: 1-5 (5=perfekt)
        - factual_consistency_normalized: 0.0-1.0
        - reasoning: Begründung
    """
    prompt = f"""Du bist ein Evaluator für Frage-Antwort-Systeme.

### Aufgabe
Bewerte die faktische Übereinstimmung der generierten Antwort mit der Referenz-Antwort.

### Frage
{query}

### Referenz-Antwort (Gold Standard)
{gold_answer}

### Generierte Antwort (zu bewerten)
{response}

### Bewertungsskala (1-5)
5 = Perfekt: Faktisch identisch, alle Punkte korrekt
4 = Gut: Überwiegend korrekt, minimale Auslassungen
3 = Akzeptabel: Kernaussagen korrekt, einige Lücken
2 = Problematisch: Wichtige Fakten fehlen oder falsch
1 = Falsch: Widersprüche oder grobe Fehler

### Antwortformat (JSON)
{{
    "score": <1-5>,
    "reasoning": "Kurze Begründung"
}}"""

    raw_response = _ollama_generate_judge(prompt, model=model)
    parsed = _parse_judge_response(raw_response)

    score = parsed.get("score", 3)
    if isinstance(score, str):
        try:
            score = int(score)
        except ValueError:
            score = 3

    score = max(1, min(5, score))

    return {
        "factual_consistency_score": score,
        "factual_consistency_normalized": (score - 1) / 4.0,  # 0.0 - 1.0
        "reasoning": parsed.get("reasoning", ""),
    }
