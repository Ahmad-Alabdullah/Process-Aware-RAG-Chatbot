"""
Query Guardrails für Process-Aware RAG.

Basiert auf State-of-the-Art 2025:
- "Building Guardrails for RAG Systems" (Medium, 2025)
- "Intent-First RAG Architecture" (2025)
- "Handling Off-Topic Queries in Conversational AI" (ScoutOS, 2025)

Implementiert Input-Guardrails zur Query-Klassifikation vor der RAG-Pipeline.
"""

from enum import Enum
from typing import Tuple
import logging

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
    "wie geht", "wie gehts", "wie gehts dir", "wie steht es", "wie stehts",
    "was machst du", "wer bist du", "wie heißt du", "was kannst du", "was bist du",
    "erzähl mir was", "langweilig", "lustig", "alles klar", "na",
]

# Process-Keywords für schnelle positive Klassifikation
PROCESS_KEYWORDS = [
    # HR/Personal
    "elternzeit", "mutterschutz", "dienstreise", "urlaub", "krankmeldung",
    "arbeitszeit", "teilzeit", "homeoffice", "gehalt", "lohn",
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
    
    # 4) Chitchat-Pattern Check
    for pattern in CHITCHAT_PATTERNS:
        if pattern in query_lower:
            logger.debug(f"Query '{query}' classified as CHITCHAT (pattern)")
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
    
    # Fallback: assume process-related
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
