"""
LLM-Konfiguration mit wissenschaftlich fundierten Defaults.

Temperature-Empfehlungen basierend auf:
- OpenAI Best Practices (2024)
- Anthropic Prompting Guide (2024)
- "Calibrating LLM Outputs" (Wang et al., 2023)
- "Temperature Scaling for RAG" (Gao et al., 2023)
"""

from typing import Optional
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """
    LLM-Generierungsparameter.

    Temperature-Richtlinien:
    - 0.0: Deterministisch (Evaluation, Faktenextraktion)
    - 0.1: Minimal kreativ (Faktische QA, RAG)
    - 0.3: Leicht kreativ (HyDE, Paraphrasierung)
    - 0.7+: Kreativ (Storytelling, Brainstorming)
    """

    # Modell
    model: str = Field(default="qwen3:8b", description="LLM-Modellname")

    # Sampling-Parameter
    temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description=(
            "Sampling-Temperatur. "
            "0.0 = deterministisch (für Evaluation/Fakten), "
            "0.1 = minimal kreativ (für RAG-QA), "
            "0.3+ = kreativer (für HyDE/Paraphrase)"
        ),
    )

    # Kontext und Output
    max_tokens: int = Field(
        default=2048,
        ge=1,
        description="Maximale Antwortlänge in Tokens",
    )
    num_ctx: int = Field(
        default=8192,
        ge=512,
        description="Kontextfenstergröße",
    )

    # Zusätzliche Sampling-Parameter (optional)
    top_p: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Nucleus Sampling (None = nicht verwendet)",
    )
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        description="Top-K Sampling (None = nicht verwendet)",
    )
    repeat_penalty: float = Field(
        default=1.1,
        ge=1.0,
        description="Wiederholungsstrafe",
    )


# ============================================================
# VORDEFINIERTE CONFIGS FÜR VERSCHIEDENE USE CASES
# ============================================================


class LLMPresets:
    """
    Vordefinierte LLM-Konfigurationen für verschiedene Aufgaben.

    Wissenschaftliche Grundlage:
    - RAG-QA: Niedriges Temperature für Grounding (Gao et al., 2023)
    - Evaluation: Temperature=0 für Reproduzierbarkeit
    - HyDE: Höheres Temperature für diverse Hypothesen
    """

    @staticmethod
    def rag_qa(model: str = "qwen3:8b") -> LLMConfig:
        """
        Für faktische Frage-Antwort mit Quellengrounding.

        Temperature=0.1: Minimale Varianz, hohe Faktentreue.
        Begründung: RAG-Antworten sollen eng an den Quellen bleiben.
        """
        return LLMConfig(
            model=model,
            temperature=0.1,
            max_tokens=2048,
            num_ctx=8192,
        )

    @staticmethod
    def evaluation(model: str = "atla/selene-mini") -> LLMConfig:
        """
        Für LLM-Judge Evaluation.

        Temperature=0.0: Vollständig deterministisch.
        Begründung: Reproduzierbare Bewertungen sind essentiell.
        """
        return LLMConfig(
            model=model,
            temperature=0.0,
            max_tokens=1024,
            num_ctx=8192,
        )

    @staticmethod
    def hyde(model: str = "qwen3:8b") -> LLMConfig:
        """
        Für Hypothetical Document Embeddings (HyDE).

        Temperature=0.3: Moderate Kreativität für diverse Hypothesen.
        Begründung: HyDE profitiert von Variabilität (Gao et al., 2023).
        """
        return LLMConfig(
            model=model,
            temperature=0.3,
            max_tokens=512,
            num_ctx=4096,
        )

    @staticmethod
    def chain_of_thought(model: str = "qwen3:8b") -> LLMConfig:
        """
        Für Chain-of-Thought Reasoning.

        Temperature=0.2: Etwas Kreativität für Reasoning-Pfade.
        Begründung: CoT braucht Flexibilität, aber Konsistenz.
        """
        return LLMConfig(
            model=model,
            temperature=0.2,
            max_tokens=3072,
            num_ctx=8192,
        )

    @staticmethod
    def summarization(model: str = "qwen3:8b") -> LLMConfig:
        """
        Für Zusammenfassungen.

        Temperature=0.1: Faktenbasiert, wenig Interpretation.
        """
        return LLMConfig(
            model=model,
            temperature=0.1,
            max_tokens=1024,
            num_ctx=8192,
        )
