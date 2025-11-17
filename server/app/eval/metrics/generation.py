from __future__ import annotations
from typing import List, Dict, Any, Tuple
import re

_WORD = re.compile(r"\w+", re.UNICODE)


def _normalize(s: str) -> List[str]:
    return _WORD.findall(s.lower())


def exact_match_f1(pred: str, gold_list: List[str]) -> Tuple[float, float]:
    pred_norm = " ".join(_normalize(pred))
    em = 1.0 if any(pred_norm == " ".join(_normalize(g)) for g in gold_list) else 0.0
    pred_tokens = _normalize(pred)
    best_f1 = 0.0
    for g in gold_list:
        gold_tokens = _normalize(g)
        common = len(set(pred_tokens) & set(gold_tokens))
        if common == 0:
            f1 = 0.0
        else:
            precision = common / len(set(pred_tokens)) if pred_tokens else 0.0
            recall = common / len(set(gold_tokens)) if gold_tokens else 0.0
            f1 = (
                2 * precision * recall / (precision + recall)
                if (precision + recall)
                else 0.0
            )
        best_f1 = max(best_f1, f1)
    return em, best_f1


def split_into_claims(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p]


def ais_heuristic(answer_text: str, cited_chunk_ids: List[str]) -> float:
    claims = split_into_claims(answer_text)
    if not claims:
        return 0.0
    if not cited_chunk_ids:
        return 0.0
    supported = 0.0
    for c in claims:
        if re.search(
            r"\[(?:DOC|CIT|REF).*?\]|Quelle|citation|\(siehe|vgl\.", c, re.IGNORECASE
        ):
            supported += 1.0
        else:
            supported += 0.5
    return supported / len(claims)
