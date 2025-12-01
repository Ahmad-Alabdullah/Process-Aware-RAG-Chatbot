from __future__ import annotations
from typing import List, Dict, Any, Tuple
import re

# generation:
#     - SemanticSim       # Embedding-basierte semantische Ähnlichkeit
#     - ROUGE-L-Recall    # Wie viel der Gold-Antwort ist in der Prediction enthalten?
#     - Content-F1        # Ohne Stoppwörter
#     - BERTScore         # Token-Level Embedding-Ähnlichkeit via BERT
# faithfulness:
#     - CitationRecall    # Wie viele der Gold-Chunks wurden in der Antwort zitiert?
#     - NLI-Faithfulness  # Semantische Prüfung: Werden Claims durch Sources gestützt?
#     - CitationPrecision # Wie viele der zitierten Chunks sind relevant?

#   llm_judge:
#     - LLM-FactualConsistency  #	LLM bewertet faktische Übereinstimmung mit Gold-Antwort (Prompt-basiert, Skale: 1-5)

_WORD = re.compile(r"\w+", re.UNICODE)


def _normalize(s: str) -> List[str]:
    return _WORD.findall(s.lower())


def exact_match_f1(pred: str, gold_list: List[str]) -> Tuple[float, float]:
    # pred_norm = " ".join(_normalize(pred))
    # em = 1.0 if any(pred_norm == " ".join(_normalize(g)) for g in gold_list) else 0.0
    # pred_tokens = _normalize(pred)
    # best_f1 = 0.0
    # for g in gold_list:
    #     gold_tokens = _normalize(g)
    #     common = len(set(pred_tokens) & set(gold_tokens))
    #     if common == 0:
    #         f1 = 0.0
    #     else:
    #         precision = common / len(set(pred_tokens)) if pred_tokens else 0.0
    #         recall = common / len(set(gold_tokens)) if gold_tokens else 0.0
    #         f1 = (
    #             2 * precision * recall / (precision + recall)
    #             if (precision + recall)
    #             else 0.0
    #         )
    #     best_f1 = max(best_f1, f1)
    # return em, best_f1
    raise NotImplementedError("exact_match_f1 is not implemented yet")


def split_into_claims(text: str) -> List[str]:
    # parts = re.split(r"(?<=[.!?])\s+", text.strip())
    # return [p for p in parts if p]
    return []


def ais_heuristic(answer_text: str, cited_chunk_ids: List[str]) -> float:
    # """
    # Sehr einfache Heuristik für "Attribution / Source-Awareness":

    # - Falls keine cited_chunk_ids: Score = 0.0
    # - Antwort wird in Sätze (claims) zerlegt.
    # - Jeder Claim, der explizite Zitationsmuster enthält (z. B. "[DOC1]", "Quelle", "vgl.")
    #   zählt voll (1.0), sonst halb (0.5).
    # - AIS = (Summe Claim-Scores) / (#Claims)

    # WICHTIG:
    # - Es findet KEIN semantischer Abgleich zwischen cited_chunk_ids und Gold-Evidence statt.
    # - Dies ist KEINE Ground-Truth-Faithfulness-Metrik, sondern nur ein grober Proxy,
    #   wie explizit Quellen in der Antwort erwähnt werden.
    # """
    # claims = split_into_claims(answer_text)
    # if not claims:
    #     return 0.0
    # if not cited_chunk_ids:
    #     return 0.0
    # supported = 0.0
    # for c in claims:
    #     if re.search(
    #         r"\[(?:DOC|CIT|REF).*?\]|Quelle|citation|\(siehe|vgl\.", c, re.IGNORECASE
    #     ):
    #         supported += 1.0
    #     else:
    #         supported += 0.5
    # return supported / len(claims)
    return 0.0
