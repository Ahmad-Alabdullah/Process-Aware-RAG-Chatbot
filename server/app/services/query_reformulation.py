"""
Query Reformulation für History-Aware Retrieval.

Basiert auf:
- DH-RAG: Dynamic History-aware RAG (arXiv, 2025)
- SELF-multi-RAG (ACL, 2024)
- Microsoft Generative Query Rewriting (Nov 2024)

Reformuliert vage Follow-up Fragen zu eigenständigen Suchanfragen.
"""

from typing import List, Optional
import logging

from app.core.models.askModel import ChatMessage
from app.services.llm import generate
from app.core.llm_config import LLMPresets

logger = logging.getLogger(__name__)


REFORMULATION_PROMPT = """Du bist ein Query-Reformulator für ein RAG-System über Hochschulprozesse.

Gegeben die Konversationshistorie und eine Follow-up Frage, formuliere die Frage 
so um, dass sie als eigenständige Suchanfrage funktioniert.

REGELN:
1. Ersetze Pronomen (sie, er, es, das, diese) durch konkrete Begriffe aus der Historie
2. Identifiziere das Hauptthema aus der Konversation und füge es in die Frage ein
3. Entferne Füllwörter wie "und" am Anfang
4. Gib NUR die reformulierte Frage zurück, KEINE Erklärungen

BEISPIELE:
---
Konversation:
Nutzer: Was ist Elternzeit?
Assistent: Elternzeit ist ein Schutzrecht für Eltern...

Follow-up: Wie lange dauert sie?
Eigenständige Frage: Wie lange dauert die Elternzeit?
---
Konversation:
Nutzer: Was ist Elternzeit?
Assistent: Elternzeit ermöglicht es Eltern...

Follow-up: und wie ist das zu beantragen?
Eigenständige Frage: Wie ist Elternzeit zu beantragen?
---
Konversation:
Nutzer: Was sind die Voraussetzungen für Elterngeld?
Assistent: Die Voraussetzungen sind...

Follow-up: welche Dokumente brauche ich dafür?
Eigenständige Frage: Welche Dokumente brauche ich für den Elterngeld-Antrag?
---

Jetzt reformuliere diese Frage:

Konversation:
{history}

Follow-up Frage: {query}

Eigenständige Frage:"""


def reformulate_query(
    query: str,
    chat_history: Optional[List[ChatMessage]],
    max_history_turns: int = 2,
) -> str:
    """
    Reformuliert vage Follow-up Fragen zu eigenständigen Queries.
    
    Nur aufgerufen wenn chat_history vorhanden ist.
    Verwendet qwen2.5:1.5b-instruct für minimale Latenz (~100-200ms).
    
    Args:
        query: Die aktuelle User-Frage
        chat_history: Vorherige Nachrichten
        max_history_turns: Maximale Anzahl Turns für Kontext
        
    Returns:
        Reformulierte, eigenständige Suchanfrage
    """
    # Skip if no history
    if not chat_history:
        logger.debug("No history, skipping reformulation")
        return query
    
    try:
        # Format history (last N*2 messages = N turns)
        recent_history = chat_history[-(max_history_turns * 2):]
        history_str = "\n".join(
            f"{'Nutzer' if m.role == 'user' else 'Assistent'}: {m.content[:150]}"
            for m in recent_history
        )
        
        # Generate reformulated query
        prompt = REFORMULATION_PROMPT.format(history=history_str, query=query)
        reformulated = generate(prompt, LLMPresets.fast_classification())
        reformulated = reformulated.strip()
        
        # Clean up common issues
        reformulated = reformulated.strip('"').strip("'")
        if reformulated.lower().startswith("eigenständige frage:"):
            reformulated = reformulated[20:].strip()
        
        # Validate result - reject if same as input or too short
        if reformulated and len(reformulated) > 3 and reformulated.lower() != query.lower():
            logger.info(f"Query reformulated: '{query}' -> '{reformulated}'")
            return reformulated
        else:
            logger.warning(f"Reformulation unchanged or invalid, using original")
            return query
            
    except Exception as e:
        logger.error(f"Query reformulation failed: {e}")
        return query


def should_reformulate(query: str, chat_history: Optional[List[ChatMessage]]) -> bool:
    """
    Heuristik: Soll die Query reformuliert werden?
    
    Reformulation ist nötig wenn:
    - Chat-History vorhanden
    - Query enthält Pronomen, ist sehr kurz, oder beginnt mit Konjunktion
    """
    if not chat_history:
        return False
    
    query_lower = query.lower().strip()
    words = query_lower.split()
    
    # Short queries often need context
    if len(words) <= 5:
        return True
    
    # Queries starting with "und" or "oder" are continuations
    if words[0] in ["und", "oder", "aber", "also"]:
        return True
    
    # Queries with pronouns or demonstratives need reformulation
    context_words = [
        "sie", "er", "es", "das", "diese", "dieser", "dieses",
        "welche", "welcher", "ihn", "ihm", "ihr", "dafür", "davon",
        "dabei", "dazu", "damit", "darauf", "darüber"
    ]
    if any(w in words for w in context_words):
        return True
    
    return False
