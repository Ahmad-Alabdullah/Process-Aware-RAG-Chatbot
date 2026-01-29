import time as time_module
import json
from typing import Optional, Generator
from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.models.askModel import AskBody
from app.core.prompt_builder import build_prompt
from app.services.retrieval import hybrid_search
from app.services.llm import generate, hyde_rewrite, ollama_generate_stream
from app.services.gating import compute_gating, GatingMode
from app.services.query_reformulation import reformulate_query, should_reformulate
from app.core.clients import get_logger
from app.core.config import settings
from app.core.llm_config import LLMPresets
from app.core.guardrails import classify_query, classify_query_with_context, should_use_rag, get_fallback_response, GuardrailMode, QueryIntent

router = APIRouter(prefix="/api/qa")

logger = get_logger(__name__)

# Rate limiter for expensive LLM endpoints
limiter = Limiter(key_func=get_remote_address)


@router.post("/ask")
@limiter.limit("20/minute")
def ask(
    request: Request,  # Required for rate limiter
    body: AskBody,
    # Optionale Overrides für Evaluation
    os_index: Optional[str] = Query("chunks_semantic_qwen3", description="OpenSearch Index Override"),
    qdrant_collection: Optional[str] = Query(
        "chunks_semantic_qwen3", description="Qdrant Collection Override"
    ),
    embedding_backend: Optional[str] = Query("ollama", description="'ollama' oder 'hf'"),
    embedding_model: Optional[str] = Query("qwen3-embedding:4b", description="Embedding Modellname"),
    # H1 Hypothesentest: Retrieval-Modus
    retrieval_mode: Optional[str] = Query(
        "hybrid", description="'hybrid' | 'vector_only' | 'bm25_only'"
    ),
    # LLM-Parameter (optional für Experimente)
    temperature: Optional[float] = Query(
        None, ge=0.0, le=2.0, description="Temperature Override (default: 0.1 für QA)"
    ),
    # LLM-Backend Auswahl
    llm_backend: Optional[str] = Query(
        None, description="'ollama' oder 'vllm' (default: settings.LLM_BACKEND)"
    ),
):
    """
    Process-Aware QA Endpoint.

    Modi (automatisch bestimmt):
    - NONE: Kein current_node_id → Baseline (process_name nur als Retrieval-Filter)
    - PROCESS_CONTEXT: force_process_context=True → Grober Prozessüberblick (nur Ablation)
    - GATING_ENABLED: current_node_id gesetzt → Lokaler Prozesskontext

    Temperature-Defaults (wissenschaftlich fundiert):
    - QA-Generierung: 0.1 (niedriges T für Faktentreue)
    - HyDE: 0.3 (höheres T für Variabilität)
    - CoT: 0.2 (moderates T für Reasoning)
    """
    logger.info(
        "QA /ask: query=%s, process=%s, node=%s, rerank=%s, emb=%s/%s, temp=%s",
        body.query[:50] if body.query else "",
        body.process_name,
        body.current_node_id,
        body.use_rerank,
        embedding_backend or "default",
        embedding_model or "default",
        temperature or "default",
    )

    t0 = time_module.perf_counter()

    # 1) Gating berechnen
    gating = compute_gating(
        process_name=body.process_name,
        process_id=body.process_id,
        definition_id=body.definition_id,
        current_node_id=body.current_node_id,
        roles=body.roles or [],
        force_process_context=body.force_process_context,
    )

    t1 = time_module.perf_counter()
    logger.info("Gating computation took %.3f seconds", t1 - t0)

    # logger.info(
    #     "Gating mode: %s, context_type: %s",
    #     gating.mode.value,
    #     gating.metadata.get("context_type"),
    # )

    # 2) Optional HyDE Query Transformation
    retrieval_query = body.query
    hyde_doc = None
    if body.use_hyde:
        t_hyde_start = time_module.perf_counter()
        hyde_doc = hyde_rewrite(body.query, model=body.model)
        retrieval_query = hyde_doc  # Use hypothetical document for embedding
        t_hyde_end = time_module.perf_counter()
        logger.info(
            "HyDE transformation took %.3f seconds (len=%d)",
            t_hyde_end - t_hyde_start,
            len(hyde_doc),
        )

    # 3) Retrieval mit optionalem Reranking
    ctx = hybrid_search(
        retrieval_query,  # Use HyDE-transformed query or original
        body.top_k,
        retrieval_mode=retrieval_mode or "hybrid",  # H1 Hypothesentest
        process_name=body.process_name,
        tags=body.tags or None,
        use_rerank=body.use_rerank,
        rerank_top_n=body.rerank_top_n,
        # Dynamische Config
        os_index=os_index,
        qdrant_collection=qdrant_collection,
        embedding_backend=embedding_backend or settings.EMBEDDING_BACKEND,
        embedding_model=embedding_model or settings.OLLAMA_EMBED_MODEL,
    )
    
    # DEBUG: Log retrieval mode and context for BM25 investigation
    logger.info(f"DEBUG: retrieval_mode={retrieval_mode}, ctx_count={len(ctx)}")

    t2 = time_module.perf_counter()
    logger.info(
        "Retrieval took %.3f seconds (rerank=%s, candidates=%d)",
        t2 - t1,
        body.use_rerank,
        body.rerank_top_n if body.use_rerank else body.top_k * 5,
    )

    # logger.info(f"ctx and das LLM: {ctx}")

    # logger.info("Retrieved %d chunks", len(ctx))

    # 3) Kontext aufbereiten
    context_text = "\n\n".join(
        [
            f"[{i+1}] (Quelle: {c.get('chunk_id', 'unbekannt')})\n{c.get('text', '')}"
            for i, c in enumerate(ctx)
        ]
    )

    # 4) Prompt bauen
    prompt = build_prompt(
        style=body.prompt_style,
        body=body,
        context_text=context_text,
        gating_hint=gating.prompt_hint,
    )

    t3 = time_module.perf_counter()

    # 6) LLM-Generierung mit passender Config
    if body.prompt_style == "cot":
        llm_config = LLMPresets.chain_of_thought(model=body.model)
    else:
        llm_config = LLMPresets.rag_qa(model=body.model)

    # Temperature Override falls angegeben
    if temperature is not None:
        llm_config.temperature = temperature

    answer = generate(prompt, config=llm_config, backend=llm_backend)

    t4 = time_module.perf_counter()
    logger.info(
        "⏱️ Total: %.2fs (gating=%.2f, retrieval=%.2f, prompt=%.2f, llm=%.2f)",
        t4 - t0,
        t1 - t0,
        t2 - t1,
        t3 - t2,
        t4 - t3,
    )

    # 6) Response
    response = {
        "answer": answer,
        "context": ctx,
        "gating_mode": gating.mode.value,
        "gating_hint": gating.prompt_hint,
        "gating_metadata": gating.metadata,
        "whitelist": gating.mode == GatingMode.GATING_ENABLED,
        "used_model": body.model,
        "used_hyde": body.use_hyde,
        "used_rerank": body.use_rerank,
        "used_retrieval_mode": retrieval_mode or "hybrid",  # H1 Tracking
        "used_temperature": llm_config.temperature,
        "used_llm_backend": llm_backend or settings.LLM_BACKEND,
        "top_k": body.top_k,
        "embedding_config": {
            "backend": embedding_backend or settings.EMBEDDING_BACKEND,
            "model": embedding_model or settings.EMBEDDING_MODEL,
        },
    }

    # Position-Details für GATING_ENABLED
    if gating.position and gating.position.current:
        response["position"] = {
            "current_node": gating.position.current.display_name(),
            "current_node_id": gating.position.current.id,
            "current_lane": gating.position.current.lane_name,
            "allowed_successors": [
                {
                    "name": s.display_name(),
                    "is_gateway": s.is_gateway,
                    "branches": (
                        [b.describe() for b in s.branches] if s.is_gateway else []
                    ),
                }
                for s in gating.position.successors
            ],
        }

    # Overview für PROCESS_CONTEXT (Ablation)
    if gating.overview:
        response["process_overview"] = {
            "lanes_with_tasks": gating.overview.lanes_with_tasks,
            "nodes_without_lane": gating.overview.nodes_without_lane[:10],
            "gateways": gating.overview.gateways,
        }

    return response


@router.post("/ask/stream")
@limiter.limit("20/minute")
def ask_stream(
    request: Request,  # Required for rate limiter
    body: AskBody,
    os_index: Optional[str] = Query("chunks_semantic_qwen3"),
    qdrant_collection: Optional[str] = Query("chunks_semantic_qwen3"),
    embedding_backend: Optional[str] = Query("ollama"),
    embedding_model: Optional[str] = Query("qwen3-embedding:4b"),
    retrieval_mode: Optional[str] = Query("hybrid"),
    temperature: Optional[float] = Query(None, ge=0.0, le=2.0),
):
    """
    Streaming QA Endpoint mit Server-Sent Events.

    Sendet zuerst Metadata (context, gating_mode, etc.) als JSON,
    dann die komplette LLM-Antwort als ein Event.

    Event-Format:
    - event: metadata, data: {...}
    - event: answer, data: "..."
    - event: done, data: {}
    """
    logger.info("QA /ask/stream: query=%s", body.query[:50] if body.query else "")

    # 0) Query Guardrail: Klassifiziere Query mit Chat-Kontext für Folgefragen
    # Konvertiere chat_history für Guardrail (falls vorhanden)
    guardrail_history = None
    if body.chat_history:
        guardrail_history = [
            {"role": msg.role, "content": msg.content}
            for msg in body.chat_history
        ]
    
    # Parse guardrail mode from request
    guardrail_mode = GuardrailMode(body.guardrail_mode) if body.guardrail_mode in [m.value for m in GuardrailMode] else GuardrailMode.HYBRID
    
    intent, confidence = classify_query_with_context(body.query, guardrail_history, mode=guardrail_mode)
    logger.debug(f"Query intent: {intent.value} (confidence: {confidence})")
    
    if not should_use_rag(intent):
        # Fallback-Response für Non-RAG Queries (Greetings, Chitchat, etc.)
        fallback_response = get_fallback_response(intent)
        logger.info(f"Guardrail triggered: {intent.value} -> returning fallback")
        
        def generate_fallback_events() -> Generator[str, None, None]:
            # Sende Metadata
            metadata = {
                "context": [],
                "gating_mode": "guardrail",
                "gating_hint": f"Query classified as {intent.value}",
                "gating_metadata": {"intent": intent.value, "confidence": confidence},
                "used_model": None,
                "used_hyde": False,
                "used_rerank": False,
            }
            yield f"event: metadata\ndata: {json.dumps(metadata)}\n\n"
            
            # Sende Fallback-Antwort als einzelnes Token (für sofortige Anzeige)
            yield f"event: token\ndata: {json.dumps(fallback_response)}\n\n"
            yield "event: done\ndata: {}\n\n"
        
        return StreamingResponse(
            generate_fallback_events(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    # 1) Gating berechnen
    gating = compute_gating(
        process_name=body.process_name,
        process_id=body.process_id,
        definition_id=body.definition_id,
        current_node_id=body.current_node_id,
        roles=body.roles or [],
        force_process_context=body.force_process_context,
    )

    # 2) Intent-basierte Query Reformulation
    #    FOLLOWUP → braucht Reformulation mit Chat-Context
    #    PROCESS_RELATED → eigenständige Frage, keine Reformulation nötig
    search_input = body.query
    
    # DEBUG: Log incoming chat history
    if body.chat_history:
        logger.info(f"[DEBUG] Received chat_history with {len(body.chat_history)} messages")
        for i, msg in enumerate(body.chat_history):
            logger.info(f"[DEBUG]   [{i}] {msg.role}: {msg.content[:50]}...")
    else:
        logger.info("[DEBUG] No chat_history received")
    
    # Intent-basierte Reformulation (statt Heuristik)
    if intent == QueryIntent.FOLLOWUP:
        logger.info(f"[Intent-Based] FOLLOWUP detected, reformulating query")
        search_input = reformulate_query(body.query, body.chat_history)
        logger.info(f"Query reformulated: '{body.query}' -> '{search_input}'")
    else:
        logger.info(f"[Intent-Based] {intent.name} - no reformulation needed")
    
    # 3) Optional HyDE (on reformulated query)
    if body.use_hyde:
        search_input = hyde_rewrite(search_input, model=body.model)

    # 3) Retrieval (same pattern as regular /ask endpoint)
    chunks = hybrid_search(
        search_input,  # positional: query
        body.top_k,    # positional: top_k
        retrieval_mode=retrieval_mode or "hybrid",
        process_name=body.process_name,
        tags=body.tags or None,
        use_rerank=body.use_rerank,
        rerank_top_n=body.rerank_top_n,
        os_index=os_index,
        qdrant_collection=qdrant_collection,
        embedding_backend=embedding_backend or settings.EMBEDDING_BACKEND,
        embedding_model=embedding_model or settings.OLLAMA_EMBED_MODEL,
    )

    ctx = [
        {
            "chunk_id": c["chunk_id"],
            "text": c["text"][:300],
            "score": round(c.get("rrf_score", 0), 4) if c.get("rrf_score") else None,
            "rerank_score": round(c.get("rerank_score", 0), 4) if c.get("rerank_score") else None,
            "metadata": {
                "process_name": c.get("process_name"),
                "tags": c.get("tags"),
                "page_number": c.get("page_number"),
                "section_title": c.get("section_title"),
                # Filename with fallback: file_name (from meta) > document_id > process fallback
                "filename": c.get("file_name") or (
                    f"Dokument zu {c.get('process_name')}" if c.get("process_name")
                    else "Unbekanntes Dokument"
                ),
                "title": c.get("title") or c.get("section_title"),
            },
        }
        for c in chunks
    ]
    
    # Add BPMN process as source when gating provides actual BPMN process context
    # (not for DOCS_ONLY which only uses process_name for filtering, no BPMN context)
    if gating.mode in (GatingMode.PROCESS_CONTEXT, GatingMode.GATING_ENABLED) and body.process_name:
        bpmn_source = {
            "chunk_id": f"bpmn_{body.process_id or body.process_name}",
            "text": gating.prompt_hint[:300] if gating.prompt_hint else "Prozesskontext",
            "score": None,
            "rerank_score": None,
            "metadata": {
                "source_type": "bpmn",
                "process_name": body.process_name,
                "filename": f"BPMN-Prozess: {body.process_name}",
                "title": f"Prozessmodell: {body.process_name}",
            },
        }
        ctx.insert(0, bpmn_source)
    
    # Number chunks by relevance order (from reranker) - [1] = most relevant
    # Note: LLM numbers its own citations in the answer text independently
    context_text = "\n\n---\n\n".join(
        f"[Chunk {i+1}] Quelle: {c.get('metadata', {}).get('filename', 'Dokument')}\n{c['text']}"
        for i, c in enumerate(chunks)
    )

    # 4) Prompt - only include gating_hint for modes that use BPMN context
    gating_hint_for_prompt = (
        gating.prompt_hint 
        if gating.mode in (GatingMode.PROCESS_CONTEXT, GatingMode.GATING_ENABLED) 
        else None
    )
    
    # Use reformulated query for prompt (includes context from chat history)
    original_query = body.query
    body.query = search_input
    
    prompt = build_prompt(
        style=body.prompt_style,
        body=body,
        context_text=context_text,
        gating_hint=gating_hint_for_prompt,
    )
    
    # Restore original query for logging/response
    body.query = original_query
    
    # DEBUG: Log full prompt
    logger.info(f"[DEBUG PROMPT] Full prompt:\n{'='*80}\n{prompt}\n{'='*80}")

    # 5) LLM Config (same pattern as regular /ask endpoint)
    if body.prompt_style == "cot":
        llm_config = LLMPresets.chain_of_thought(model=body.model or settings.OLLAMA_MODEL)
    else:
        llm_config = LLMPresets.rag_qa(model=body.model or settings.OLLAMA_MODEL)
    
    # Log the model being used
    logger.info(f"Using LLM model: {llm_config.model}")

    # Temperature Override falls angegeben
    if temperature is not None:
        llm_config.temperature = temperature

    # Generator für SSE - Token-by-Token Streaming
    def generate_events() -> Generator[str, None, None]:
        # Sende Metadata zuerst
        metadata = {
            "context": ctx,
            "gating_mode": gating.mode.value,
            "gating_hint": gating.prompt_hint,
            "gating_metadata": gating.metadata,
            "used_model": body.model,
            "used_hyde": body.use_hyde,
            "used_rerank": body.use_rerank,
        }
        yield f"event: metadata\ndata: {json.dumps(metadata)}\n\n"

        # Streame LLM-Antwort Token für Token
        for token in ollama_generate_stream(prompt, config=llm_config):
            yield f"event: token\ndata: {json.dumps(token)}\n\n"

        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )

