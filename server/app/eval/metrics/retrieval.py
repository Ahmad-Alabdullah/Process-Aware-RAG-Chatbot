from __future__ import annotations
from typing import List, Dict, Set
import math


def recall_at_k(ranked_ids: List[str], gold_ids: Set[str], k: int) -> float:
    """
    Recall@K: Anteil der relevanten Dokumente in den Top-K Ergebnissen.

    Args:
        ranked_ids: Gerankte chunk_ids vom Retrieval
        gold_ids: Set der relevanten chunk_ids
        k: Cutoff

    Returns:
        Recall-Wert zwischen 0.0 und 1.0
    """
    if not gold_ids:
        return 0.0
    topk = ranked_ids[:k]
    hits = sum(1 for x in topk if x in gold_ids)
    return hits / len(gold_ids)


def mrr_at_k(ranked_ids: List[str], gold_ids: Set[str], k: int) -> float:
    """
    Mean Reciprocal Rank@K: 1/Position des ersten relevanten Dokuments.

    Args:
        ranked_ids: Gerankte chunk_ids vom Retrieval
        gold_ids: Set der relevanten chunk_ids
        k: Cutoff

    Returns:
        MRR-Wert zwischen 0.0 und 1.0
    """
    for idx, x in enumerate(ranked_ids[:k], start=1):
        if x in gold_ids:
            return 1.0 / idx
    return 0.0


def _dcg(rels: List[int], k: int) -> float:
    """
    Discounted Cumulative Gain.

    DCG = Σ (2^rel - 1) / log2(i + 1)
    """
    dcg = 0.0
    for i, rel in enumerate(rels[:k], start=1):
        if rel > 0:
            dcg += (2**rel - 1) / math.log2(i + 1)
    return dcg


def ndcg_at_k(ranked_ids: List[str], gold_dict: Dict[str, int], k: int) -> float:
    """
    Normalized Discounted Cumulative Gain@K.

    Berücksichtigt gradierte Relevanz (0-3 Skala).

    Args:
        ranked_ids: Gerankte chunk_ids vom Retrieval
        gold_dict: Dict {chunk_id: relevance_score}
        k: Cutoff

    Returns:
        NDCG-Wert zwischen 0.0 und 1.0
    """
    rels = [gold_dict.get(x, 0) for x in ranked_ids[:k]]
    dcg = _dcg(rels, k)

    ideal_rels = sorted(gold_dict.values(), reverse=True)[:k]
    if not ideal_rels:
        return 0.0
    idcg = _dcg(ideal_rels, k)

    return dcg / idcg if idcg > 0 else 0.0


def compute_retrieval_metrics(
    ranked_ids: List[str], gold_dict: Dict[str, int], cutoffs: List[int] = [3, 5, 10]
) -> Dict[str, float]:
    """
    Berechnet alle Retrieval-Metriken für verschiedene Cutoffs.

    Args:
        ranked_ids: Gerankte chunk_ids vom Retrieval
        gold_dict: Dict {chunk_id: relevance_score} (0-3 Skala)
        cutoffs: Liste von K-Werten

    Returns:
        Dict mit allen Metriken
    """
    gold_ids = {k for k, v in gold_dict.items() if v > 0}

    res: Dict[str, float] = {}
    for k in cutoffs:
        res[f"recall@{k}"] = recall_at_k(ranked_ids, gold_ids, k)
        res[f"mrr@{k}"] = mrr_at_k(ranked_ids, gold_ids, k)
        res[f"ndcg@{k}"] = ndcg_at_k(ranked_ids, gold_dict, k)

    return res
