"""
Query Guardrails für Process-Aware RAG.

Basiert auf State-of-the-Art 2025:
- "Building Guardrails for RAG Systems" (Medium, 2025)
- "Intent-First RAG Architecture" (2025)
- "Handling Off-Topic Queries in Conversational AI" (ScoutOS, 2025)

Implementiert Input-Guardrails zur Query-Klassifikation vor der RAG-Pipeline.
"""

from enum import Enum
from typing import Tuple, List, Optional
import logging
import re

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """Query-Intent-Kategorien für Guardrail-Routing."""
    
    PROCESS_RELATED = "process_related"  # Valide RAG-Query
    GREETING = "greeting"  # Begrüßungen (Hi, Hallo)
    CHITCHAT = "chitchat"  # Smalltalk (Wie geht's?)
    OFF_TOPIC = "off_topic"  # Komplett unrelated
    UNCLEAR = "unclear"  # Unklare Anfrage


# LLM-Prompt für Intent-Klassifikation (nur für ambige Fälle)
INTENT_CLASSIFICATION_PROMPT = """Klassifiziere die folgende Benutzeranfrage.

Anfrage: "{query}"

Kategorien:
- PROCESS_RELATED: Frage zu Hochschulprozessen, Richtlinien, Mutterschutz, Elternzeit, Dienstreisen, Prüfungen, etc.
- GREETING: Begrüßung wie "Hallo", "Hi", "Guten Tag"
- CHITCHAT: Smalltalk wie "Wie geht's?", "Was machst du?", "Wer bist du?"
- OFF_TOPIC: Komplett unrelated (Sport, Wetter, Politik, Rezepte, etc.)
- UNCLEAR: Zu kurz oder unklar, was gemeint ist

Antworte NUR mit dem Kategorie-Namen (z.B. "PROCESS_RELATED")."""


# LLM-Prompt für Verification von unsicheren Klassifikationen
# Basiert auf "LLM as Judge" Pattern (GuardrailsAI, 2024)
INTENT_VERIFICATION_PROMPT = """Überprüfe diese Klassifikation einer Benutzeranfrage.

Anfrage: "{query}"
Vorläufige Klassifikation: {initial_intent}

WICHTIG: Sei PERMISSIV. Im Zweifel sollte die Query als prozessbezogen behandelt werden.

Prüfe:
1. Ist die Anfrage wirklich {initial_intent_description}?
2. Oder könnte es eine (auch implizite) Frage zu Hochschulprozessen sein?
3. Enthält die Anfrage Hinweise auf Verwaltungsthemen (auch wenn versteckt)?

Antworte mit GENAU einem Wort:
- CONFIRM: Die Klassifikation "{initial_intent}" ist korrekt
- OVERRIDE: Die Anfrage ist doch PROCESS_RELATED (prozessbezogen)"""


# Confidence-Threshold für LLM-Verification
# Klassifikationen unter diesem Wert werden durch LLM nachgeprüft
# Basiert auf "Hybrid NLU/LLM Intent Classification" (Voiceflow, 2024)
LLM_VERIFICATION_THRESHOLD = 0.90


# Freundliche Fallback-Antworten für Non-RAG Queries (Deutsch)
FALLBACK_RESPONSES = {
    QueryIntent.GREETING: (
        "Hallo! 👋 Ich bin der Prozessberater für Hochschulverwaltung. "
        "Ich kann Ihnen bei Fragen zu Prozessen wie Elternzeit, Mutterschutz, "
        "Dienstreisen oder anderen Verwaltungsabläufen helfen. "
        "Wie kann ich Ihnen behilflich sein?"
    ),
    QueryIntent.CHITCHAT: (
        "Danke der Nachfrage! Ich bin ein spezialisierter Assistent für Hochschulprozesse. "
        "Smalltalk liegt leider nicht in meinem Fachgebiet. 😊 "
        "Aber ich helfe Ihnen gerne bei Fragen zu Themen wie Elternzeit, Mutterschutz, "
        "Dienstreisen oder anderen Prozessen an der Hochschule."
    ),
    QueryIntent.OFF_TOPIC: (
        "Diese Frage liegt leider außerhalb meines Wissensbereichs. "
        "Ich bin auf Hochschulprozesse und -richtlinien spezialisiert. "
        "Haben Sie eine Frage zu einem bestimmten Prozess, z.B. Antragstellung, "
        "Genehmigungen oder Zuständigkeiten?"
    ),
    QueryIntent.UNCLEAR: (
        "Könnten Sie Ihre Frage bitte etwas präziser formulieren? "
        "Ich helfe Ihnen gerne bei Themen wie Antragsprozessen, Richtlinien, "
        "Mutterschutz, Elternzeit oder anderen Hochschulverwaltungsthemen."
    ),
}


# Pattern-basierte Erkennung für häufige Fälle (schneller als LLM)
GREETING_PATTERNS = [
    "hi", "hallo", "hey", "guten tag", "guten morgen", "guten abend",
    "moin", "servus", "grüß gott", "hello", "grüezi"
]

CHITCHAT_PATTERNS = [
    # Spezifischere Patterns - keine kurzen Substrings mehr
    "wie geht es", "wie gehts", "wie gehts dir", "wie steht es", "wie stehts",
    "was machst du", "wer bist du", "wie heißt du", "was kannst du", "was bist du",
]

# Process-Keywords für schnelle positive Klassifikation
PROCESS_KEYWORDS = [
    # HR/Personal
    "elternzeit", "mutterschutz", "dienstreise", "urlaub", "krankmeldung",
    "arbeitszeit", "teilzeit", "homeoffice", "gehalt", "lohn", "ALPAKA", 
    "Mentoring", "Projekt", "Professor", "Tandemprogramm", "Onboarding",
    "Evaluation", "Feedback", "Akkreditierung", "Studiengang", "Qualitätsmanagement",
    "Qualifikation", "Qualifizierung", "HAWKarriere", "HAW", "Mentees", "Mentor",
    "Benefits", 
    # Anträge
    "antrag", "formular", "genehmigung", "unterschrift", "freigabe",
    # Prozesse
    "prozess", "ablauf", "workflow", "schritt", "zuständigkeit",
    # Hochschule
    "hochschule", "hka", "studium", "prüfung", "immatrikulation",
    "exmatrikulation", "anrechnung", "semester", "vorlesung",
    "notenumrechnung", "studienleistung", "creditpoints",
    # Richtlinien
    "richtlinie", "vorschrift", "regelung", "gesetz", "verordnung",
]


def classify_query(query: str) -> Tuple[QueryIntent, float]:
    """
    Klassifiziert eine Benutzeranfrage.
    
    Hybrid-Ansatz:
    1. Pattern-Matching für offensichtliche Fälle (0ms, 95%+ der Queries)
    2. LLM-Klassifikation nur für ambige Fälle (100-200ms, 5% der Queries)
    
    WICHTIG: Process-Keywords werden ZUERST geprüft, um False Positives zu vermeiden.
    Z.B. "Hallo, ich möchte über Elterngeld wissen" → PROCESS_RELATED (nicht GREETING)
    
    Args:
        query: Die Benutzeranfrage
        
    Returns:
        Tuple[QueryIntent, confidence]: Intent und Konfidenz (0.0-1.0)
    """
    query_lower = query.lower().strip()
    query_len = len(query_lower)
    
    # 1) ZUERST: Process-Keyword Check (höchste Priorität)
    # Damit "Hallo, ich möchte über Elterngeld wissen" als PROCESS erkannt wird
    for keyword in PROCESS_KEYWORDS:
        if keyword in query_lower:
            logger.debug(f"Query '{query}' classified as PROCESS_RELATED (keyword: {keyword})")
            return QueryIntent.PROCESS_RELATED, 0.95
    
    # 2) Sehr kurze Queries (< 5 Zeichen) ohne Keywords sind oft Greetings
    if query_len < 5:
        for pattern in GREETING_PATTERNS:
            if query_lower == pattern or query_lower.startswith(pattern):
                logger.debug(f"Query '{query}' classified as GREETING (short pattern)")
                return QueryIntent.GREETING, 0.95
        return QueryIntent.UNCLEAR, 0.8
    
    # 3) "Pure" Greeting Check - nur wenn Query kurz und NUR Greeting enthält
    if query_len < 30:
        for pattern in GREETING_PATTERNS:
            # Exakte Matches oder Greeting am Anfang mit wenig danach
            if query_lower == pattern or query_lower == pattern + "!":
                logger.debug(f"Query '{query}' classified as GREETING (exact)")
                return QueryIntent.GREETING, 0.95
            # Greeting + kurzer Rest ohne Fragezeichen
            if query_lower.startswith(pattern) and "?" not in query_lower and query_len < 15:
                logger.debug(f"Query '{query}' classified as GREETING (short)")
                return QueryIntent.GREETING, 0.9
    
    # 4) Chitchat-Pattern Check (Substring-Match für längere Patterns)
    for pattern in CHITCHAT_PATTERNS:
        if pattern in query_lower:
            logger.debug(f"Query '{query}' classified as CHITCHAT (pattern: {pattern})")
            return QueryIntent.CHITCHAT, 0.9
    
    # 5) Frage-Wörter deuten auf echte Frage hin
    question_starters = ["was ", "wie ", "wer ", "wann ", "wo ", "warum ", "welche", "können ", "muss ", "darf "]
    has_question = any(query_lower.startswith(q) or f" {q}" in query_lower for q in question_starters)
    
    if has_question and query_len > 15:
        logger.debug(f"Query '{query}' classified as PROCESS_RELATED (question heuristic)")
        return QueryIntent.PROCESS_RELATED, 0.7
    
    # 6) Für ambige Fälle: LLM-Klassifikation mit schnellem Modell
    logger.debug(f"Query '{query}' ambiguous, using LLM classification")
    return classify_query_with_llm(query)


def classify_query_with_llm(query: str) -> Tuple[QueryIntent, float]:
    """
    Klassifiziert Query mittels LLM (für ambige Fälle).
    
    Nur verwenden wenn Pattern-Matching unsicher ist.
    Fügt ~200-500ms Latenz hinzu.
    """
    from app.services.llm import generate
    from app.core.llm_config import LLMPresets
    
    try:
        prompt = INTENT_CLASSIFICATION_PROMPT.format(query=query)
        response = generate(prompt, LLMPresets.fast_classification())
        response = response.strip().upper().replace(" ", "_")
        
        for intent in QueryIntent:
            if intent.name in response:
                logger.debug(f"Query '{query}' classified as {intent.name} (LLM)")
                return intent, 0.85
                
    except Exception as e:
        logger.warning(f"LLM classification failed: {e}")
    
    # Fallback: assume process-related (permissiv)
    return QueryIntent.PROCESS_RELATED, 0.5


# Beschreibungen für Intent-Typen (für Verification-Prompt)
INTENT_DESCRIPTIONS = {
    QueryIntent.GREETING: "eine reine Begrüßung ohne Frage",
    QueryIntent.CHITCHAT: "Smalltalk ohne Bezug zu Hochschulprozessen",
    QueryIntent.OFF_TOPIC: "eine Frage zu einem komplett anderen Thema",
    QueryIntent.UNCLEAR: "eine unklare oder zu kurze Anfrage",
}


def verify_with_llm(query: str, initial_intent: QueryIntent, confidence: float) -> Tuple[QueryIntent, float]:
    """
    LLM-Verification für unsichere Pattern-Klassifikationen.
    
    Basiert auf "LLM as Judge" Pattern (GuardrailsAI, 2024):
    - Pattern-Match mit niedriger Confidence wird durch LLM nachgeprüft
    - LLM kann die Entscheidung überschreiben (zu PROCESS_RELATED)
    - Permissiver Ansatz: Im Zweifel → prozessbezogen
    
    Args:
        query: Die Benutzeranfrage
        initial_intent: Die Pattern-basierte Klassifikation
        confidence: Die Confidence der Pattern-Klassifikation
        
    Returns:
        Tuple[QueryIntent, float]: Finale Intent-Klassifikation mit Confidence
    """
    from app.services.llm import generate
    from app.core.llm_config import LLMPresets
    
    # Nur Non-PROCESS Klassifikationen werden verifiziert
    if initial_intent == QueryIntent.PROCESS_RELATED:
        return initial_intent, confidence
    
    # Hohe Confidence → keine Verification nötig
    if confidence >= LLM_VERIFICATION_THRESHOLD:
        logger.debug(f"Skipping LLM verification: confidence {confidence} >= threshold {LLM_VERIFICATION_THRESHOLD}")
        return initial_intent, confidence
    
    logger.info(f"LLM verification triggered for '{query[:50]}...' (intent={initial_intent.name}, conf={confidence})")
    
    try:
        prompt = INTENT_VERIFICATION_PROMPT.format(
            query=query,
            initial_intent=initial_intent.name,
            initial_intent_description=INTENT_DESCRIPTIONS.get(initial_intent, "unbekannt")
        )
        
        response = generate(prompt, LLMPresets.fast_classification())
        response = response.strip().upper()
        
        if "OVERRIDE" in response:
            logger.info(f"LLM OVERRIDE: '{query[:50]}...' is PROCESS_RELATED (was {initial_intent.name})")
            return QueryIntent.PROCESS_RELATED, 0.8
        elif "CONFIRM" in response:
            logger.debug(f"LLM CONFIRM: '{query[:50]}...' is {initial_intent.name}")
            return initial_intent, min(confidence + 0.1, 0.95)  # Boost confidence after LLM confirmation
        else:
            logger.warning(f"LLM verification unclear response: {response}")
            # Bei unklarer Antwort: Permissiv → PROCESS_RELATED
            return QueryIntent.PROCESS_RELATED, 0.6
            
    except Exception as e:
        logger.warning(f"LLM verification failed: {e}")
        # Bei Fehler: Permissiv → PROCESS_RELATED
        return QueryIntent.PROCESS_RELATED, 0.5


def should_use_rag(intent: QueryIntent) -> bool:
    """
    Prüft ob Query durch RAG-Pipeline verarbeitet werden soll.
    
    Nur PROCESS_RELATED Queries gehen durch RAG.
    Alle anderen bekommen Fallback-Antworten.
    """
    return intent == QueryIntent.PROCESS_RELATED


def get_fallback_response(intent: QueryIntent) -> str:
    """
    Gibt passende Fallback-Antwort für Non-RAG Queries.
    
    Returns:
        Benutzerfreundliche deutsche Antwort
    """
    return FALLBACK_RESPONSES.get(intent, FALLBACK_RESPONSES[QueryIntent.UNCLEAR])


def classify_query_with_context(
    query: str,
    chat_history: Optional[List[dict]] = None
) -> Tuple[QueryIntent, float]:
    """
    Kontext-bewusste Query-Klassifikation mit LLM-Verification.
    
    Hybrid-Ansatz basiert auf:
    - "Contextual Query Understanding in RAG" (2025)
    - "Hybrid NLU/LLM Intent Classification" (Voiceflow, 2024)
    - "LLM as Judge" Pattern (GuardrailsAI, 2024)
    
    Flow:
    1. Context-Check (Follow-up Patterns, Chat-History)
    2. Pattern-basierte Klassifikation
    3. LLM-Verification für unsichere Non-PROCESS Klassifikationen
    
    Args:
        query: Die aktuelle Benutzeranfrage
        chat_history: Liste von {"role": "user"|"assistant", "content": str}
        
    Returns:
        Tuple[QueryIntent, confidence]: Intent und Konfidenz
    """
    query_lower = query.lower().strip()
    
    # Follow-up Patterns die auf Kontext-Bezug hindeuten
    FOLLOWUP_PATTERNS = [
        "nochmal", "noch mal", "nochmals", "erneut",
        "kannst du", "könntest du", "können sie", "könnten sie",
        "bitte prüfen", "bitte nochmal", "bitte noch mal",
        "mehr dazu", "mehr informationen", "mehr details",
        "genauer", "präziser", "ausführlicher",
        "was meinst du", "wie meinst du",
        "und was ist mit", "was ist mit",
        "das verstehe ich nicht", "erkläre", "erklär",
    ]
    
    logger.info(f"[Context Check] chat_history: {len(chat_history) if chat_history else 0} messages")
    
    # ========================================
    # SCHRITT 1: Follow-up Pattern Check (hohe Priorität)
    # ========================================
    if chat_history and len(chat_history) >= 2:
        if len(query_lower) < 60:
            for pattern in FOLLOWUP_PATTERNS:
                if pattern in query_lower:
                    logger.info(f"Query '{query[:50]}...' classified as PROCESS_RELATED (follow-up pattern: '{pattern}')")
                    return QueryIntent.PROCESS_RELATED, 0.8
    
    # ========================================
    # SCHRITT 2: Pattern-based Classification
    # ========================================
    intent, confidence = classify_query(query)
    logger.info(f"[Pattern] Query classified as {intent.name} (conf={confidence})")
    
    # ========================================
    # SCHRITT 3: Context-based Boost (nur für AMBIGE Fälle)
    # ========================================
    # WICHTIG: Klare Chitchat/Greeting Queries werden NICHT durch Context überschrieben
    # Nur bei niedriger Confidence hilft der Context
    if chat_history and len(chat_history) >= 2:
        if intent != QueryIntent.PROCESS_RELATED and confidence < 0.85:
            # Prüfe ob vorherige Antwort substantiell war
            last_assistant = None
            for msg in reversed(chat_history):
                if msg.get("role") == "assistant":
                    last_assistant = msg
                    break
            
            if last_assistant:
                content = last_assistant.get("content", "")
                # Nur Context-Boost wenn wir unsicher sind UND vorherige Antwort RAG-artig war
                if len(content) > 200:  # Höherer Threshold für Context-Boost
                    logger.info(
                        f"[Context Boost] Query '{query[:50]}...' upgraded to PROCESS_RELATED "
                        f"(was {intent.name}, conf={confidence}, prev_response={len(content)} chars)"
                    )
                    return QueryIntent.PROCESS_RELATED, 0.7
    
    # ========================================
    # SCHRITT 4: LLM Verification (Hybrid Approach)
    # ========================================
    # Nur Non-PROCESS Klassifikationen mit niedriger Confidence werden verifiziert
    if intent != QueryIntent.PROCESS_RELATED and confidence < LLM_VERIFICATION_THRESHOLD:
        logger.info(f"[Hybrid] Pattern classified as {intent.name} (conf={confidence}), triggering LLM verification")
        final_intent, final_confidence = verify_with_llm(query, intent, confidence)
        return final_intent, final_confidence
    
    return intent, confidence

