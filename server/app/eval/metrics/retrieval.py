from __future__ import annotations
from typing import List, Dict, Set
import math


def recall_at_k(ranked_ids: List[str], gold_ids: Set[str], k: int) -> float:
    if not gold_ids:
        return 0.0
    topk = ranked_ids[:k]
    hit = sum(1 for x in topk if x in gold_ids)
    return hit / len(gold_ids)


def mrr_at_k(ranked_ids: List[str], gold_ids: Set[str], k: int) -> float:
    for idx, x in enumerate(ranked_ids[:k], start=1):
        if x in gold_ids:
            return 1.0 / idx
    return 0.0


def _dcg(rels: List[int], k: int) -> float:
    dcg = 0.0
    for i, rel in enumerate(rels[:k], start=1):
        if rel > 0:
            dcg += (2**rel - 1) / math.log2(i + 1)
    return dcg


def ndcg_at_k(ranked_ids: List[str], gold_dict: Dict[str, int], k: int) -> float:
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
    gold_ids = {k for k, v in gold_dict.items() if v > 0}
    res: Dict[str, float] = {}
    for k in cutoffs:
        res[f"recall@{k}"] = recall_at_k(ranked_ids, gold_ids, k)
        res[f"mrr@{k}"] = mrr_at_k(ranked_ids, gold_ids, k)
        res[f"ndcg@{k}"] = ndcg_at_k(ranked_ids, gold_dict, k)
    return res
