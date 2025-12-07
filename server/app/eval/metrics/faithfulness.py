from __future__ import annotations
from typing import List, Dict, Set, Optional
import re

from app.core.clients import get_logger

logger = get_logger(__name__)


# ============================================================
# CITATION RECALL & PRECISION
# ============================================================


def citation_recall(
    cited_chunk_ids: List[str],
    gold_chunk_ids: Set[str],
) -> float:
    """
    Citation Recall: Wie viele der Gold-Chunks wurden zitiert?
    """
    if not gold_chunk_ids:
        return 1.0

    if not cited_chunk_ids:
        return 0.0

    cited_set = set(cited_chunk_ids)
    hits = len(cited_set & gold_chunk_ids)

    return hits / len(gold_chunk_ids)


def citation_precision(
    cited_chunk_ids: List[str],
    gold_chunk_ids: Set[str],
) -> float:
    """
    Citation Precision: Wie viele der zitierten Chunks sind relevant?
    """
    if not cited_chunk_ids:
        return 1.0

    cited_set = set(cited_chunk_ids)
    hits = len(cited_set & gold_chunk_ids)

    return hits / len(cited_set)


# ============================================================
# HAUPTFUNKTION
# ============================================================


def compute_faithfulness_metrics(
    cited_chunk_ids: List[str],
    gold_chunk_ids: Set[str],
) -> Dict[str, float]:
    """
    Berechnet alle Faithfulness-Metriken.

    Metriken:
    - CitationRecall: Wie viele Gold-Chunks wurden zitiert?
    - CitationPrecision: Wie viele zitierte Chunks sind relevant?
    - NLI-Faithfulness: Werden Claims durch Sources gestützt?
    """
    results: Dict[str, float] = {}

    # Citation-Metriken
    results["citation_recall"] = citation_recall(cited_chunk_ids, gold_chunk_ids)
    results["citation_precision"] = citation_precision(cited_chunk_ids, gold_chunk_ids)

    return results
