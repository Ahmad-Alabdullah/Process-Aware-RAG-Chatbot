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


def semantic_similarity(pred: str, gold: str) -> float:
    """
    Embedding-basierte semantische Ähnlichkeit.

    Verwendet EmbeddingGemma-300m via Ollama (unabhängig von Pipeline).
    """
    if not pred.strip() or not gold.strip():
        return 0.0

    try:
        import requests
        from app.core.config import settings

        resp = requests.post(
            f"{settings.OLLAMA_BASE}/api/embed",
            json={
                "model": "EmbeddingGemma:300m",
                "input": [pred, gold],
            },
            timeout=60,
        )
        resp.raise_for_status()
        embeddings = resp.json()["embeddings"]

        # Kosinus-Ähnlichkeit
        pred_emb = np.array(embeddings[0])
        gold_emb = np.array(embeddings[1])

        # Normalisieren
        pred_norm = pred_emb / (np.linalg.norm(pred_emb) + 1e-9)
        gold_norm = gold_emb / (np.linalg.norm(gold_emb) + 1e-9)

        similarity = float(np.dot(pred_norm, gold_norm))
        return max(0.0, similarity)

    except Exception as e:
        logger.warning(f"Semantic similarity (EmbeddingGemma) Fehler: {e}")
        return 0.0


# ============================================================
# BERTSCORE
# ============================================================

_bertscore_model = None


def _get_bertscore():
    """Lazy Loading von BERTScore."""
    global _bertscore_model
    if _bertscore_model is None:
        try:
            from bert_score import BERTScorer
            import torch

            device = "cuda" if torch.cuda.is_available() else "cpu"

            _bertscore_model = BERTScorer(
                lang="de",
                rescale_with_baseline=True,
                device=device,
                model_type="deepset/gbert-large",
                num_layers=17,
            )
            logger.info("BERTScore geladen (lang=de)")
        except Exception as e:
            logger.warning(f"BERTScore init Fehler: {e}")
            return None
    return _bertscore_model


def bert_score(pred: str, gold: str) -> Dict[str, float]:
    """
    BERTScore: Token-Level Embedding-Ähnlichkeit via BERT.
    """
    if not pred.strip() or not gold.strip():
        return {
            "bertscore_precision": 0.0,
            "bertscore_recall": 0.0,
            "bertscore_f1": 0.0,
        }

    scorer = _get_bertscore()
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


def compute_generation_metrics(pred: str, gold: str) -> Dict[str, float]:
    """
    Berechnet alle Generation-Metriken.

    Metriken:
    - SemanticSim: Embedding-basierte Ähnlichkeit
    - ROUGE-L-Recall: Wie viel der Gold-Antwort ist enthalten?
    - Content-F1: Token-F1 ohne Stoppwörter
    - BERTScore: Token-Level Embedding-Ähnlichkeit
    """
    results: Dict[str, float] = {}

    if not pred or not gold:
        return results

    # Content-F1
    results["content_f1"] = content_f1(pred, gold)

    # ROUGE-L (nur Recall für deine Zwecke)
    rouge = rouge_l(pred, gold)
    results["rouge_l_recall"] = rouge["rouge_l_recall"]

    # Semantic Similarity
    results["semantic_sim"] = semantic_similarity(pred, gold)

    # BERTScore
    bert = bert_score(pred, gold)
    results["bertscore_f1"] = bert["bertscore_f1"]

    return results
