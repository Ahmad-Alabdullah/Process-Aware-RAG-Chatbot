"""
Prompt Builder für Process-Aware RAG.

Basiert auf:
- "Prompting Guidelines for LLMs" (OpenAI, Anthropic)
- "RAFT: Adapting Language Model to Domain Specific RAG" (Zhang et al., 2024)
- "Lost in the Middle" (Liu et al., 2023) - Kontext-Positionierung
- "Chain-of-Thought Prompting" (Wei et al., 2022)
"""

from typing import Optional
from app.core.models.askModel import AskBody


# ============================================================
# SYSTEM PROMPTS (Rollen-Definition)
# ============================================================

SYSTEM_PROMPT_DE = """Du bist ein Experte für Hochschulprozesse und Verwaltungsabläufe.
Deine Aufgabe ist es, Fragen zu Prozessen, Richtlinien und Zuständigkeiten präzise zu beantworten.

WICHTIGE REGELN:
1. Antworte NUR basierend auf den bereitgestellten Dokumenten und dem Prozesskontext.
2. Zitiere relevante Quellen mit [1], [2], etc.
3. Wenn die Informationen nicht ausreichen, sage es ehrlich.
4. Erfinde KEINE Informationen."""

SYSTEM_PROMPT_GATING = """Du bist ein Prozessberater für Hochschulverwaltung.
Du beantwortest Fragen im Kontext einer SPEZIFISCHEN Position im Prozess.

WICHTIGE REGELN:
1. Beachte den Prozesskontext (aktuelle Position, Rolle, erlaubte Schritte).
2. Beschränke dich auf relevante Informationen für die aktuelle Situation.
3. Zitiere Quellen mit [1], [2], etc.
4. Erfinde KEINE Prozessschritte oder Zuständigkeiten."""


# ============================================================
# PROMPT TEMPLATES
# ============================================================


def _format_context_block(context_text: str) -> str:
    """Formatiert den Kontext-Block mit klarer Struktur."""
    if not context_text.strip():
        return "Keine relevanten Dokumente gefunden."
    return context_text


def _format_gating_block(gating_hint: str, style: str) -> str:
    """Formatiert den Gating-Hint mit Erklärung."""
    if not gating_hint or style == "no_gating":
        return ""

    return f"""
### Prozesskontext (BEACHTEN!)
{gating_hint}

⚠️ Beschränke deine Antwort auf diesen Kontext. Erwähne keine Schritte außerhalb des erlaubten Bereichs."""


def build_prompt(
    style: str,
    body: AskBody,
    context_text: str,
    gating_hint: str,
) -> str:
    """
    Erzeugt den finalen Prompt basierend auf dem Stil.

    Styles:
    - baseline: Standard RAG mit Gating
    - no_gating: RAG ohne Prozesskontext (Ablation)
    - fewshot: Mit Beispielen
    - cot: Chain-of-Thought Reasoning
    - structured: Strukturierte Antwort mit Abschnitten
    - citation_first: Erst zitieren, dann antworten (bessere Faithfulness)
    """

    if style == "baseline":
        return _build_baseline_prompt(body, context_text, gating_hint)
    elif style == "no_gating":
        return _build_no_gating_prompt(body, context_text)
    elif style == "fewshot":
        return _build_fewshot_prompt(body, context_text, gating_hint)
    elif style == "cot":
        return _build_cot_prompt(body, context_text, gating_hint)
    elif style == "structured":
        return _build_structured_prompt(body, context_text, gating_hint)
    elif style == "citation_first":
        return _build_citation_first_prompt(body, context_text, gating_hint)
    else:
        return _build_baseline_prompt(body, context_text, gating_hint)


# ============================================================
# BASELINE PROMPT (Optimiert)
# ============================================================


def _build_baseline_prompt(
    body: AskBody,
    context_text: str,
    gating_hint: str,
) -> str:
    """
    Optimierter Baseline-Prompt nach Best Practices.

    Struktur (nach Liu et al., 2023 "Lost in the Middle"):
    1. System-Instruktion (oben)
    2. Kontext/Dokumente (Mitte - wichtigstes zuerst)
    3. Gating-Hint (vor Frage)
    4. Frage (unten - höchste Aufmerksamkeit)
    5. Output-Format (ganz unten)
    """
    gating_block = _format_gating_block(gating_hint, "baseline")

    return f"""{SYSTEM_PROMPT_GATING if gating_hint else SYSTEM_PROMPT_DE}

### Relevante Dokumente
{_format_context_block(context_text)}
{gating_block}

### Frage
{body.query}

### Antwort
Beantworte die Frage präzise und vollständig auf Deutsch.
- Zitiere relevante Stellen mit [1], [2], etc.
- Strukturiere die Antwort klar und übersichtlich.
- Wenn Informationen fehlen, sage: "Basierend auf den vorliegenden Dokumenten kann ich dazu keine Aussage treffen."

Antwort:"""


# ============================================================
# NO GATING PROMPT (Ablation - Baseline ohne Prozesskontext)
# ============================================================


def _build_no_gating_prompt(
    body: AskBody,
    context_text: str,
) -> str:
    """
    Prompt ohne Gating-Kontext für Ablation-Study.
    Testet: Was passiert ohne Prozesskontext?
    """
    return f"""{SYSTEM_PROMPT_DE}

### Relevante Dokumente
{_format_context_block(context_text)}

### Frage
{body.query}

### Antwort
Beantworte die Frage präzise und vollständig auf Deutsch.
- Zitiere relevante Stellen mit [1], [2], etc.
- Strukturiere die Antwort klar.
- Bei fehlenden Informationen: "Basierend auf den Dokumenten kann ich dazu keine Aussage treffen."

Antwort:"""


# ============================================================
# FEW-SHOT PROMPT (Mit Beispielen)
# ============================================================

# Domänenspezifische Beispiele für besseres In-Context Learning
FEWSHOT_EXAMPLES = """
### Beispiel 1: Zuständigkeitsfrage
**Frage:** Wer genehmigt Dienstreisen an der Hochschule?
**Kontext:** [1] "Dienstreisen werden vom direkten Vorgesetzten genehmigt. Bei Reisen ins Ausland ist zusätzlich die Zustimmung der Hochschulleitung erforderlich."
**Antwort:** Dienstreisen werden vom direkten Vorgesetzten genehmigt [1]. Bei Auslandsreisen ist zusätzlich die Zustimmung der Hochschulleitung notwendig [1].

### Beispiel 2: Prozessfrage mit Kontext
**Prozesskontext:** Sie befinden sich im Schritt "Antrag prüfen" als Sachbearbeiter.
**Frage:** Was muss ich bei der Antragsprüfung beachten?
**Kontext:** [1] "Der Sachbearbeiter prüft die Vollständigkeit der Unterlagen und die formale Korrektheit."
**Antwort:** Als Sachbearbeiter im Schritt "Antrag prüfen" müssen Sie die Vollständigkeit der Unterlagen sowie die formale Korrektheit überprüfen [1].

### Beispiel 3: Keine ausreichenden Informationen
**Frage:** Wie hoch ist das Budget für Forschungsreisen?
**Kontext:** [1] "Dienstreisen müssen vorab beantragt werden."
**Antwort:** Basierend auf den vorliegenden Dokumenten kann ich zur Höhe des Budgets für Forschungsreisen keine Aussage treffen. Die Dokumente enthalten nur Informationen zum Antragsverfahren [1]."""


def _build_fewshot_prompt(
    body: AskBody,
    context_text: str,
    gating_hint: str,
) -> str:
    """
    Few-Shot Prompt mit domänenspezifischen Beispielen.

    Basiert auf: Brown et al. (2020) "Language Models are Few-Shot Learners"
    """
    gating_block = _format_gating_block(gating_hint, "fewshot")

    return f"""{SYSTEM_PROMPT_GATING if gating_hint else SYSTEM_PROMPT_DE}

Hier sind Beispiele für gute Antworten:
{FEWSHOT_EXAMPLES}

---

Jetzt beantworte die folgende Frage im gleichen Stil:

### Relevante Dokumente
{_format_context_block(context_text)}
{gating_block}

### Frage
{body.query}

### Antwort
Antwort:"""


# ============================================================
# CHAIN-OF-THOUGHT PROMPT
# ============================================================


def _build_cot_prompt(
    body: AskBody,
    context_text: str,
    gating_hint: str,
) -> str:
    """
    Chain-of-Thought Prompt für komplexe Fragen.

    Basiert auf: Wei et al. (2022) "Chain-of-Thought Prompting"

    Verwendet <think>-Tags für internes Reasoning (werden später entfernt).
    """
    gating_block = _format_gating_block(gating_hint, "cot")

    return f"""{SYSTEM_PROMPT_GATING if gating_hint else SYSTEM_PROMPT_DE}

### Relevante Dokumente
{_format_context_block(context_text)}
{gating_block}

### Frage
{body.query}

### Anleitung
Beantworte die Frage in zwei Schritten:

1. **Denke zuerst nach** (in <think>-Tags, wird dem Nutzer nicht gezeigt):
   - Welche Dokumente sind relevant?
   - Was ist der Prozesskontext?
   - Welche Informationen fehlen?

2. **Formuliere dann die Antwort**:
   - Präzise und strukturiert
   - Mit Zitaten [1], [2], etc.
   - Auf Deutsch

<think>
Schritt 1: Relevante Informationen identifizieren...
Schritt 2: Prozesskontext beachten...
Schritt 3: Antwort strukturieren...
</think>

Antwort:"""


# ============================================================
# STRUCTURED PROMPT (Für komplexe Prozessfragen)
# ============================================================


def _build_structured_prompt(
    body: AskBody,
    context_text: str,
    gating_hint: str,
) -> str:
    """
    Strukturierter Prompt für umfassende Prozessantworten.

    Erzwingt eine klare Gliederung der Antwort.
    """
    gating_block = _format_gating_block(gating_hint, "structured")

    return f"""{SYSTEM_PROMPT_GATING if gating_hint else SYSTEM_PROMPT_DE}

### Relevante Dokumente
{_format_context_block(context_text)}
{gating_block}

### Frage
{body.query}

### Antwortformat
Strukturiere deine Antwort wie folgt:

**Zusammenfassung:** (1-2 Sätze Kernaussage)

**Details:**
- Punkt 1 mit Beleg [X]
- Punkt 2 mit Beleg [X]

**Zuständigkeiten:** (falls relevant)
- Rolle: Aufgabe

**Hinweise:** (falls relevant)
- Besonderheiten oder Ausnahmen

Antwort:"""


# ============================================================
# CITATION-FIRST PROMPT (Für bessere Faithfulness)
# ============================================================


def _build_citation_first_prompt(
    body: AskBody,
    context_text: str,
    gating_hint: str,
) -> str:
    """
    Citation-First Prompt für verbesserte Faithfulness.

    Basiert auf:
    - Gao et al. (2023) "Enabling Large Language Models to Generate Text with Citations"
    - ALCE Benchmark (Attributable to Identified Sources)

    Kernidee: Das LLM soll ERST relevante Zitate extrahieren,
    DANN eine Antwort formulieren. Dies verhindert Halluzinationen,
    da jede Aussage direkt an eine Quelle gebunden wird.

    Vorteile:
    - Höhere factual_consistency (AlignScore)
    - Bessere citation_precision
    - Weniger Paraphrasierung → näher am Originaltext
    """
    gating_block = _format_gating_block(gating_hint, "citation_first")

    return f"""{SYSTEM_PROMPT_GATING if gating_hint else SYSTEM_PROMPT_DE}

### Relevante Dokumente
{_format_context_block(context_text)}
{gating_block}

### Frage
{body.query}

### Anleitung (Citation-First)
Beantworte die Frage in ZWEI SCHRITTEN:

**SCHRITT 1: Relevante Zitate extrahieren**
Identifiziere zunächst die relevanten Passagen aus den Dokumenten.
Formatiere sie als:
- [1]: "Exaktes Zitat aus Dokument 1..."
- [2]: "Exaktes Zitat aus Dokument 2..."
(Nur Zitate, die direkt zur Beantwortung der Frage beitragen)

**SCHRITT 2: Antwort formulieren**
Formuliere basierend auf den extrahierten Zitaten eine präzise Antwort.
Jede Aussage MUSS durch ein Zitat [X] belegt sein.

### Antwort
**Relevante Zitate:**

**Antwort:**"""


# ============================================================
# HILFSFUNKTIONEN
# ============================================================


def extract_answer_from_cot(response: str) -> str:
    """
    Entfernt <think>-Tags aus CoT-Antworten.

    Gibt nur die finale Antwort zurück.
    """
    import re

    # Entferne <think>...</think> Blöcke
    cleaned = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL)

    # Entferne führende/trailing Whitespace
    cleaned = cleaned.strip()

    # Entferne "Antwort:" Prefix falls vorhanden
    if cleaned.lower().startswith("antwort:"):
        cleaned = cleaned[8:].strip()

    return cleaned
