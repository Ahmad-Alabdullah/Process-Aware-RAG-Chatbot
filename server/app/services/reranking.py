"""
Reranking-Service mit BGE Reranker v2-m3.

Modell: BAAI/bge-reranker-v2-m3
- Multilingual (inkl. Deutsch)
- Bis zu 8192 Tokens Kontext
- Cross-Encoder Architektur
- Weniger VRAM-Verbrauch als Jina v3
"""

from __future__ import annotations
from typing import List, Dict, Any
import threading
import torch

from app.core.clients import get_logger

logger = get_logger(__name__)

_reranker_model = None
_reranker_lock = threading.Lock()
_compute_lock = threading.Lock()  # Serialize GPU inference to prevent CUDA race conditions


def _get_reranker():
    """Lazy Loading des BGE Reranker v2-m3 Modells (Thread-safe)."""
    global _reranker_model
    
    # Double-checked locking pattern for thread safety
    if _reranker_model is None:
        with _reranker_lock:
            # Check again inside lock
            if _reranker_model is None:
                try:
                    from FlagEmbedding import FlagReranker

                    model_name = "BAAI/bge-reranker-v2-m3"
                    use_fp16 = torch.cuda.is_available()

                    _reranker_model = {
                        "model": FlagReranker(
                            model_name,
                            use_fp16=use_fp16,
                        ),
                        "device": "cuda" if torch.cuda.is_available() else "cpu",
                    }
                    logger.info(f"BGE Reranker v2-m3 geladen (fp16={use_fp16})")
                except Exception as e:
                    logger.error(f"BGE Reranker v2-m3 konnte nicht geladen werden: {e}")
                    return None
    return _reranker_model


def unload_reranker():
    """Entlädt den Reranker aus dem GPU-Speicher, um Platz für Ollama zu machen."""
    global _reranker_model
    if _reranker_model is not None:
        try:
            del _reranker_model["model"]
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
    Rerankt Dokumente mit BGE Reranker v2-m3 Cross-Encoder.

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
        
        # Query-Document Paare erstellen
        pairs = [[query, doc.get(text_key, "")] for doc in documents]
        
        # FlagReranker.compute_score() is not thread-safe on GPU
        # Serialize inference calls to prevent CUDA race conditions
        with _compute_lock:
            scores = model.compute_score(pairs, normalize=True)
        
        # Falls nur ein Dokument, ist scores ein Float statt Liste
        if isinstance(scores, (int, float)):
            scores = [scores]
        
        # Scores mit Indizes kombinieren und sortieren
        scored_indices = list(enumerate(scores))
        scored_indices.sort(key=lambda x: x[1], reverse=True)
        
        # Top-K auswählen und Original-Dokumente anreichern
        ranked_docs = []
        for idx, score in scored_indices[:top_k]:
            doc_copy = documents[idx].copy()
            doc_copy["rerank_score"] = float(score)
            doc_copy["source"] = "ce"
            ranked_docs.append(doc_copy)

        top_scores = ", ".join(f"{d['rerank_score']:.3f}" for d in ranked_docs[:3])
        logger.debug(
            f"Reranking: {len(documents)} docs → top {top_k}, scores: [{top_scores}]"
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
