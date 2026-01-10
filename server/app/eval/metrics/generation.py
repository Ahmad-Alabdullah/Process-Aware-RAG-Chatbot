from __future__ import annotations
from typing import List, Dict, Tuple
import re
import numpy as np

from app.core.clients import get_logger

logger = get_logger(__name__)

_WORD = re.compile(r"\w+", re.UNICODE)

# Deutsche Stoppwörter für Content-F1
GERMAN_STOPWORDS = {
    "der",
    "die",
    "das",
    "den",
    "dem",
    "des",
    "ein",
    "eine",
    "einer",
    "eines",
    "und",
    "oder",
    "aber",
    "wenn",
    "weil",
    "dass",
    "ob",
    "als",
    "wie",
    "ist",
    "sind",
    "war",
    "waren",
    "wird",
    "werden",
    "wurde",
    "wurden",
    "hat",
    "haben",
    "hatte",
    "hatten",
    "kann",
    "können",
    "muss",
    "müssen",
    "soll",
    "sollen",
    "will",
    "wollen",
    "darf",
    "dürfen",
    "ich",
    "du",
    "er",
    "sie",
    "es",
    "wir",
    "ihr",
    "mein",
    "dein",
    "sein",
    "unser",
    "euer",
    "dieser",
    "diese",
    "dieses",
    "jener",
    "jene",
    "jenes",
    "nicht",
    "auch",
    "nur",
    "noch",
    "schon",
    "sehr",
    "mehr",
    "mit",
    "von",
    "zu",
    "bei",
    "nach",
    "für",
    "aus",
    "an",
    "auf",
    "in",
    "über",
    "unter",
    "vor",
    "hinter",
    "neben",
    "zwischen",
    "durch",
    "gegen",
    "ohne",
    "um",
    "hier",
    "dort",
    "da",
    "wo",
    "wann",
    "warum",
    "was",
    "wer",
    "welche",
    "welcher",
    "so",
    "also",
    "doch",
    "ja",
    "nein",
    "vielleicht",
    "etwa",
    "wohl",
}


def _normalize(s: str) -> List[str]:
    """Tokenisiert und normalisiert Text."""
    return _WORD.findall(s.lower())


def _normalize_without_stopwords(s: str) -> List[str]:
    """Tokenisiert, normalisiert und entfernt Stoppwörter."""
    tokens = _WORD.findall(s.lower())
    return [t for t in tokens if t not in GERMAN_STOPWORDS]


# ============================================================
# CONTENT-F1 (Ohne Stoppwörter)
# ============================================================


def content_f1(pred: str, gold: str) -> float:
    """
    Content-F1: Token-F1 ohne Stoppwörter.

    Fokussiert auf inhaltstragende Wörter.
    """
    pred_tokens = set(_normalize_without_stopwords(pred))
    gold_tokens = set(_normalize_without_stopwords(gold))

    if not pred_tokens or not gold_tokens:
        return 0.0

    common = len(pred_tokens & gold_tokens)
    if common == 0:
        return 0.0

    precision = common / len(pred_tokens)
    recall = common / len(gold_tokens)

    return 2 * precision * recall / (precision + recall)


# ============================================================
# ROUGE-L
# ============================================================


def _lcs_length(a: List[str], b: List[str]) -> int:
    """Longest Common Subsequence Länge."""
    m, n = len(a), len(b)
    if m == 0 or n == 0:
        return 0

    prev = [0] * (n + 1)
    curr = [0] * (n + 1)

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev, curr = curr, prev

    return prev[n]


def rouge_l(pred: str, gold: str) -> Dict[str, float]:
    """
    ROUGE-L: Longest Common Subsequence basierte Metrik.

    Returns:
        Dict mit precision, recall, f1
    """
    pred_tokens = _normalize(pred)
    gold_tokens = _normalize(gold)

    if not pred_tokens or not gold_tokens:
        return {"rouge_l_precision": 0.0, "rouge_l_recall": 0.0, "rouge_l_f1": 0.0}

    lcs_len = _lcs_length(pred_tokens, gold_tokens)

    precision = lcs_len / len(pred_tokens)
    recall = lcs_len / len(gold_tokens)

    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)

    return {
        "rouge_l_precision": precision,
        "rouge_l_recall": recall,
        "rouge_l_f1": f1,
    }


# ============================================================
# SEMANTIC SIMILARITY (EmbeddingGemma-300m)
# ============================================================

# _semantic_model = None


# def _get_semantic_model():
#     """Lazy Loading von EmbeddingGemma-300m."""
#     global _semantic_model
#     if _semantic_model is None:
#         from sentence_transformers import SentenceTransformer

#         try:
#             _semantic_model = SentenceTransformer(
#                 "Snowflake/snowflake-arctic-embed-m-v2.0"
#             )
#             logger.info("Loaded Snowflake Arctic Embed for SemanticSim")
#         except Exception as e:
#             logger.warning(f"Arctic Embed nicht verfügbar, fallback zu MiniLM: {e}")
#             _semantic_model = SentenceTransformer(
#                 "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
#             )
#     return _semantic_model


def semantic_similarity(
    pred: str, gold: str, model: str = "embeddinggemma:latest"
) -> float:
    """
    Embedding-basierte semantische Ähnlichkeit.
    """
    if not pred.strip() or not gold.strip():
        return 0.0

    try:
        import requests
        from app.core.config import settings

        resp = requests.post(
            f"{settings.OLLAMA_BASE}/api/embed",
            json={
                "model": model,
                "input": [pred, gold],
            },
            timeout=60,
        )
        resp.raise_for_status()
        embeddings = resp.json()["embeddings"]

        pred_emb = np.array(embeddings[0])
        gold_emb = np.array(embeddings[1])

        pred_norm = pred_emb / (np.linalg.norm(pred_emb) + 1e-9)
        gold_norm = gold_emb / (np.linalg.norm(gold_emb) + 1e-9)

        similarity = float(np.dot(pred_norm, gold_norm))
        return max(0.0, similarity)

    except Exception as e:
        logger.warning(f"Semantic similarity Fehler: {e}")
        return 0.0


# ============================================================
# BERTSCORE
# ============================================================

import threading
_bertscore_models = {}
_bertscore_lock = threading.Lock()


def _get_bertscore(model: str = "deepset/gbert-large"):
    """Lazy Loading von BERTScore mit konfiguriertem Modell (Thread-safe)."""
    global _bertscore_models

    if model not in _bertscore_models:
        with _bertscore_lock:
            # Double-check inside lock
            if model not in _bertscore_models:
                try:
                    from bert_score import BERTScorer
                    import torch

                    device = "cuda" if torch.cuda.is_available() else "cpu"

                    # num_layers basierend auf Modell
                    num_layers = 17 if "large" in model.lower() else 9

                    _bertscore_models[model] = BERTScorer(
                        model_type=model,
                        lang="de",
                        num_layers=num_layers,
                        rescale_with_baseline=False,  # No baseline available for gbert-large
                        device=device,
                    )
                    logger.info(f"BERTScore geladen (model={model}, device={device})")
                except Exception as e:
                    logger.warning(f"BERTScore init Fehler: {e}")
                    return None

    return _bertscore_models.get(model)


def bert_score(
    pred: str, gold: str, model: str = "deepset/gbert-large"
) -> Dict[str, float]:
    """BERTScore mit konfiguriertem Modell."""
    if not pred.strip() or not gold.strip():
        return {
            "bertscore_precision": 0.0,
            "bertscore_recall": 0.0,
            "bertscore_f1": 0.0,
        }

    scorer = _get_bertscore(model)
    if scorer is None:
        return {
            "bertscore_precision": 0.0,
            "bertscore_recall": 0.0,
            "bertscore_f1": 0.0,
        }

    try:
        P, R, F1 = scorer.score([pred], [gold])
        return {
            "bertscore_precision": float(P[0]),
            "bertscore_recall": float(R[0]),
            "bertscore_f1": float(F1[0]),
        }
    except Exception as e:
        logger.warning(f"BERTScore Fehler: {e}")
        return {
            "bertscore_precision": 0.0,
            "bertscore_recall": 0.0,
            "bertscore_f1": 0.0,
        }


# ============================================================
# HAUPTFUNKTION
# ============================================================


def compute_generation_metrics(
    pred: str,
    gold: str,
    semantic_sim_model: str = "embeddinggemma:latest",
    bertscore_model: str = "deepset/gbert-large",
) -> Dict[str, float]:
    """
    Berechnet alle Generation-Metriken.

    Args:
        pred: Generierte Antwort
        gold: Gold-Antwort
        semantic_sim_model: Modell für SemanticSim (via Ollama)
        bertscore_model: Modell für BERTScore
    """
    results: Dict[str, float] = {}

    if not pred or not gold:
        return results

    # Content-F1
    results["content_f1"] = content_f1(pred, gold)

    # ROUGE-L
    rouge = rouge_l(pred, gold)
    results["rouge_l_recall"] = rouge["rouge_l_recall"]

    # Semantic Similarity (mit konfiguriertem Modell)
    results["semantic_sim"] = semantic_similarity(pred, gold, model=semantic_sim_model)

    # BERTScore (mit konfiguriertem Modell)
    bert = bert_score(pred, gold, model=bertscore_model)
    results["bertscore_f1"] = bert["bertscore_f1"]

    return results
