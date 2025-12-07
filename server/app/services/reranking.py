"""
Reranking-Service mit Jina Reranker v3.

Modell: jinaai/jina-reranker-v3
- Multilingual (inkl. Deutsch)
- Bis zu 8192 Tokens Kontext
- Cross-Encoder Architektur
"""

from __future__ import annotations
from typing import List, Dict, Any
import torch

from app.core.clients import get_logger

logger = get_logger(__name__)

_reranker_model = None


def _get_reranker():
    """Lazy Loading des Jina Reranker v3 Modells."""
    global _reranker_model
    if _reranker_model is None:
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            model_name = "jinaai/jina-reranker-v3"
            device = "cuda" if torch.cuda.is_available() else "cpu"

            _reranker_model = {
                "tokenizer": AutoTokenizer.from_pretrained(
                    model_name, trust_remote_code=True
                ),
                "model": AutoModelForSequenceClassification.from_pretrained(
                    model_name, trust_remote_code=True, torch_dtype=torch.float16
                ).to(device),
                "device": device,
            }
            logger.info(f"Jina Reranker v3 geladen (device={device})")
        except Exception as e:
            logger.error(f"Jina Reranker v3 konnte nicht geladen werden: {e}")
            return None
    return _reranker_model


def rerank(
    query: str,
    documents: List[Dict[str, Any]],
    top_k: int = 5,
    text_key: str = "text",
) -> List[Dict[str, Any]]:
    """
    Rerankt Dokumente mit Jina Reranker v3 Cross-Encoder.

    Args:
        query: Suchanfrage
        documents: Liste von Dokumenten mit 'text' Feld
        top_k: Anzahl der zurückzugebenden Dokumente
        text_key: Key für den Text in den Dokumenten

    Returns:
        Rerankte Dokumente mit 'rerank_score' Feld, sortiert nach Score
    """
    if not documents:
        return []

    if not query.strip():
        logger.warning("Leere Query für Reranking, überspringe")
        return documents[:top_k]

    reranker = _get_reranker()
    if reranker is None:
        logger.warning("Reranker nicht verfügbar, gebe Original-Reihenfolge zurück")
        # Fallback: Original-Reihenfolge mit Placeholder-Scores
        for i, doc in enumerate(documents[:top_k]):
            doc["rerank_score"] = 1.0 - (i * 0.1)
            doc["source"] = "rrf"
        return documents[:top_k]

    try:
        tokenizer = reranker["tokenizer"]
        model = reranker["model"]
        device = reranker["device"]

        # Paare erstellen: (query, document_text)
        texts = [doc.get(text_key, "") for doc in documents]
        pairs = [[query, text] for text in texts]

        # Tokenisieren
        with torch.no_grad():
            inputs = tokenizer(
                pairs,
                padding=True,
                truncation=True,
                max_length=8192,
                return_tensors="pt",
            ).to(device)

            # Scores berechnen
            outputs = model(**inputs)
            scores = outputs.logits.squeeze(-1).cpu().tolist()

            # Falls nur ein Dokument, ist scores ein float
            if isinstance(scores, float):
                scores = [scores]

        # Scores zu Dokumenten hinzufügen
        scored_docs = []
        for doc, score in zip(documents, scores):
            doc_copy = doc.copy()
            doc_copy["rerank_score"] = float(score)
            doc_copy["source"] = "ce"  # Cross-Encoder
            scored_docs.append(doc_copy)

        # Nach Score sortieren (höher = besser)
        ranked = sorted(scored_docs, key=lambda x: x["rerank_score"], reverse=True)

        logger.debug(
            f"Reranking: {len(documents)} docs → top {top_k}, "
            f"scores: [{', '.join(f'{d['rerank_score']:.3f}' for d in ranked[:3])}]"
        )

        return ranked[:top_k]

    except Exception as e:
        logger.error(f"Reranking Fehler: {e}")
        # Fallback: Original-Reihenfolge
        for i, doc in enumerate(documents[:top_k]):
            doc["rerank_score"] = 0.0
            doc["source"] = "rrf"
        return documents[:top_k]


def rerank_batch(
    queries: List[str],
    documents_per_query: List[List[Dict[str, Any]]],
    top_k: int = 5,
    text_key: str = "text",
) -> List[List[Dict[str, Any]]]:
    """
    Batch-Reranking für mehrere Queries.

    Args:
        queries: Liste von Suchanfragen
        documents_per_query: Liste von Dokument-Listen (eine pro Query)
        top_k: Anzahl der zurückzugebenden Dokumente pro Query
        text_key: Key für den Text in den Dokumenten

    Returns:
        Liste von gerankten Dokument-Listen
    """
    results = []
    for query, docs in zip(queries, documents_per_query):
        ranked = rerank(query, docs, top_k, text_key)
        results.append(ranked)
    return results
