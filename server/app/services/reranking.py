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
            from transformers import AutoModel, AutoTokenizer

            model_name = "jinaai/jina-reranker-v3"
            device = "cuda" if torch.cuda.is_available() else "cpu"

            _reranker_model = {
                "tokenizer": AutoTokenizer.from_pretrained(
                    model_name, trust_remote_code=True
                ),
                "model": AutoModel.from_pretrained(
                    model_name, trust_remote_code=True, dtype=torch.float16
                ).to(device),
                "device": device,
            }
            # Qwen3-basierte Modelle haben kein pad_token
            if _reranker_model["tokenizer"].pad_token is None:
                _reranker_model["tokenizer"].pad_token = _reranker_model["tokenizer"].eos_token
                logger.info(f"pad_token gesetzt auf: {_reranker_model['tokenizer'].pad_token}")
            logger.info(f"Jina Reranker v3 geladen (device={device})")
        except Exception as e:
            logger.error(f"Jina Reranker v3 konnte nicht geladen werden: {e}")
            return None
    return _reranker_model


def unload_reranker():
    """Entlädt den Reranker aus dem GPU-Speicher, um Platz für Ollama zu machen."""
    global _reranker_model
    if _reranker_model is not None:
        try:
            del _reranker_model["model"]
            del _reranker_model["tokenizer"]
            _reranker_model = None
            
            # GPU Cache leeren
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
            
            logger.info("Reranker aus GPU-Speicher entladen")
        except Exception as e:
            logger.warning(f"Fehler beim Entladen des Rerankers: {e}")


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
        model = reranker["model"]
        
        # Texte extrahieren
        texts = [doc.get(text_key, "") for doc in documents]
        
        # returns list of dicts: {'document': str, 'relevance_score': float, 'index': int}
        results = model.rerank(query, texts, max_query_length=512, max_doc_length=4096)
        
        # Sortieren nach Score (höher = besser)
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        # Top-K auswählen und Original-Dokumente anreichern
        ranked_docs = []
        for res in results[:top_k]:
            idx = res["index"]
            score = float(res["relevance_score"])
            
            doc_copy = documents[idx].copy()
            doc_copy["rerank_score"] = score
            doc_copy["source"] = "ce"
            ranked_docs.append(doc_copy)

        logger.debug(
            f"Reranking: {len(documents)} docs → top {top_k}, "
            f"scores: [{', '.join(f'{d['rerank_score']:.3f}' for d in ranked_docs[:3])}]"
        )
        
        return ranked_docs

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
