"""
Synthetic Evaluation Data Generator using RAGAS.

Generiert synthetische Query-Answer-Paare aus existierenden Chunks
für die RAG-Evaluation.

Basiert auf:
- RAGAS TestsetGenerator (Evol-Instruct Paradigma)
- Verwendet separates Generator-LLM für Bias-Vermeidung
"""

import json
from pathlib import Path
from typing import List, Dict, Any
import typer

from langchain_ollama import OllamaLLM, OllamaEmbeddings
from ragas.testset import TestsetGenerator
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

from app.core.clients import get_logger, get_opensearch, setup_logging
from app.core.config import settings

logger = get_logger(__name__)
app = typer.Typer()


def load_chunks_from_opensearch(
    index_name: str = "chunks_semantic_qwen3",
    max_chunks: int = 300,
) -> List[Dict[str, Any]]:
    """
    Lädt existierende Chunks aus OpenSearch.
    
    Returns:
        List of dicts with 'content', 'chunk_id', 'document_id'
    """
    client = get_opensearch()
    
    # Suche alle Chunks
    response = client.search(
        index=index_name,
        body={
            "query": {"match_all": {}},
            "size": max_chunks,
            "_source": ["text", "document_id", "meta"]  # Actual field names in index
        }
    )
    
    chunks = []
    for hit in response["hits"]["hits"]:
        source = hit["_source"]
        # Map to our expected format
        chunks.append({
            "content": source.get("text", ""),  # text -> content
            "chunk_id": hit["_id"],  # Use _id as chunk_id
            "document_id": source.get("document_id", "unknown"),
            "metadata": source.get("meta", {}),
        })
    
    logger.info(f"Loaded {len(chunks)} chunks from {index_name}")
    return chunks


def chunks_to_documents(chunks: List[Dict[str, Any]], min_length: int = 400) -> List[str]:
    """
    Konvertiert Chunks zu Dokumenten für RAGAS.
    
    Args:
        chunks: Liste von Chunks
        min_length: Minimale Chunk-Länge in Zeichen (RAGAS braucht >100 Tokens)
    """
    from langchain_core.documents import Document
    
    docs = []
    skipped = 0
    for chunk in chunks:
        content = chunk["content"]
        # Filter short chunks - RAGAS requires at least 100 tokens
        if len(content) < min_length:
            skipped += 1
            continue
        doc = Document(
            page_content=content,
            metadata={
                "chunk_id": chunk["chunk_id"],
                "document_id": chunk["document_id"],
            }
        )
        docs.append(doc)
    
    if skipped > 0:
        logger.info(f"Skipped {skipped} chunks shorter than {min_length} chars")
    
    return docs


def generate_synthetic_testset(
    documents: List[Any],
    generator_model: str = "qwen3:8b",
    embedding_model: str = "qwen3-embedding:4b",
    num_samples: int = 20,
) -> List[Dict[str, Any]]:
    """
    Generiert synthetischen Testset mit RAGAS.
    
    Args:
        documents: Liste von LangChain Documents
        generator_model: Ollama Modell für Frage-Generierung
        embedding_model: Ollama Modell für Embeddings
        num_samples: Anzahl der zu generierenden Samples
        
    Returns:
        List of dicts with 'query', 'reference_answer', 'reference_chunks'
    """
    import asyncio
    from ragas.testset.persona import Persona
    
    logger.info(f"Setting up RAGAS TestsetGenerator with {generator_model}")
    
    # Build content -> chunk_id mapping for later qrels extraction
    # Use multiple prefix lengths for better matching
    content_to_chunk_id = {}
    for doc in documents:
        chunk_id = doc.metadata.get("chunk_id", "unknown")
        # Store multiple prefix lengths for fuzzy matching
        for prefix_len in [50, 100, 150, 200]:
            prefix = doc.page_content[:prefix_len].strip()
            if prefix:
                content_to_chunk_id[prefix] = chunk_id
        # Also store full content hash
        content_to_chunk_id[doc.page_content.strip()] = chunk_id
    
    # LLM Setup - Zwei unterschiedliche Temperatures
    # KG-Extraktion: niedrig (0.2) für präzise Entity-Extraction
    kg_llm = OllamaLLM(
        model=generator_model,
        temperature=0.2,
        format="json",
        system="Du bist ein deutscher Assistent. Extrahiere Informationen präzise auf Deutsch."
    )
    
    # Q&A Generation: etwas höher (0.5) für natürliche Fragen
    qa_llm = OllamaLLM(
        model=generator_model,
        temperature=0.5,
        format="json",
        system="Du bist ein deutscher Assistent. Generiere IMMER Fragen und Antworten auf Deutsch. Niemals auf Englisch antworten."
    )
    
    embeddings = OllamaEmbeddings(model=embedding_model)
    
    # RAGAS Wrapper - separate für KG und Generation
    kg_llm_wrapped = LangchainLLMWrapper(kg_llm)
    generator_llm = LangchainLLMWrapper(qa_llm)
    generator_embeddings = LangchainEmbeddingsWrapper(embeddings)
    
    # Personas für deutschen Hochschul-Kontext
    personas = [
        Persona(
            name="Hochschulmitarbeiter",
            role_description="Ein Verwaltungsmitarbeiter, der Fragen zu HR-Prozessen und Anträgen hat",
        ),
        Persona(
            name="Professor",
            role_description="Ein Professor, der Fragen zu Forschungssemestern, Lehrverpflichtungen und Drittmitteln hat",
        ),
        Persona(
            name="Rektoratsmitglied",
            role_description="Ein Mitglied des Rektorats, der strategische Fragen zu Richtlinien und Regularien hat",
        ),
    ]
    
    # Custom Knowledge Graph Builder (bypasses broken RAGAS transforms)
    from app.eval.knowledge_graph_builder import build_knowledge_graph
    
    logger.info("Building custom knowledge graph with LLM property extraction (temp=0.2)...")
    knowledge_graph = build_knowledge_graph(
        documents=documents,
        llm=kg_llm_wrapped,  # Niedriger Temperature für präzise Extraktion
        embedding_model=generator_embeddings,
        similarity_threshold=0.5,  # Niedrigerer Threshold für mehr Vielfalt
    )
    
    # TestsetGenerator mit Personas und deutschem Kontext
    generator = TestsetGenerator(
        llm=generator_llm,
        embedding_model=generator_embeddings,
        persona_list=personas,
        knowledge_graph=knowledge_graph,  # Pre-built KG
        llm_context="WICHTIG: Generiere ALLE Fragen und Antworten ausschließlich auf Deutsch. "
                    "Verwende deutsche Grammatik, Rechtschreibung und Fachbegriffe. "
                    "Niemals auf Englisch antworten.",
    )
    
    # All-in-One Query-Distribution mit Fokus auf Multi-Hop
    from ragas.testset.synthesizers.multi_hop.abstract import MultiHopAbstractQuerySynthesizer
    from ragas.testset.synthesizers.multi_hop.specific import MultiHopSpecificQuerySynthesizer
    from ragas.testset.synthesizers.single_hop.specific import SingleHopSpecificQuerySynthesizer
    
    distribution = [
        (MultiHopSpecificQuerySynthesizer(llm=generator_llm), 0.35),    # 35% Multi-Hop faktenbasiert
        (MultiHopAbstractQuerySynthesizer(llm=generator_llm), 0.35),    # 35% Multi-Hop abstrakt
        (SingleHopSpecificQuerySynthesizer(llm=generator_llm), 0.30),   # 30% Single-Hop einfach
    ]
    
    # Adapt prompts für Deutsch
    logger.info("Adapting prompts for German language...")
    async def adapt_prompts_async():
        for query, _ in distribution:
            prompts = await query.adapt_prompts("german", llm=generator_llm)
            query.set_prompts(**prompts)
    
    asyncio.run(adapt_prompts_async())
    
    logger.info(f"Generating {num_samples} synthetic Q&A pairs (with skip-on-error)...")
    
    # Generate samples iteratively to handle errors gracefully
    # This allows us to skip failed samples and continue with the rest
    all_samples_df = []
    failed_count = 0
    
    for sample_idx in range(num_samples):
        try:
            # Generate single sample
            single_testset = generator.generate(
                testset_size=1,
                query_distribution=distribution,
            )
            
            # Convert to dataframe and accumulate
            df = single_testset.to_pandas()
            if len(df) > 0:
                all_samples_df.append(df)
                logger.info(f"Generated sample {len(all_samples_df)}/{num_samples}")
            
        except Exception as e:
            failed_count += 1
            logger.warning(f"Sample {sample_idx+1} failed (skipping): {str(e)[:100]}...")
            continue
    
    # Combine all successful samples
    import pandas as pd
    if all_samples_df:
        combined_df = pd.concat(all_samples_df, ignore_index=True)
        logger.info(f"Successfully generated {len(combined_df)} samples ({failed_count} failed)")
    else:
        combined_df = pd.DataFrame()
        logger.warning("No samples were generated successfully!")
    
    # Create a mock testset object with the combined dataframe
    class MockTestset:
        def __init__(self, df):
            self._df = df
        def to_pandas(self):
            return self._df
        def __len__(self):
            return len(self._df)
    
    testset = MockTestset(combined_df)
    
    # Convert to our format with proper chunk_id extraction
    samples = []
    for i, row in enumerate(testset.to_pandas().itertuples()):
        # Extract chunk_ids from reference_contexts by matching content
        reference_chunk_ids = []
        contexts = row.reference_contexts if hasattr(row, 'reference_contexts') else []
        for ctx in contexts:
            if not isinstance(ctx, str) or not ctx.strip():
                continue
            
            # Try multiple matching strategies
            chunk_id = None
            ctx_clean = ctx.strip()
            
            # Strategy 1: Exact full match
            if ctx_clean in content_to_chunk_id:
                chunk_id = content_to_chunk_id[ctx_clean]
            
            # Strategy 2: Try different prefix lengths
            if not chunk_id:
                for prefix_len in [200, 150, 100, 50]:
                    prefix = ctx_clean[:prefix_len].strip()
                    if prefix in content_to_chunk_id:
                        chunk_id = content_to_chunk_id[prefix]
                        break
            
            # Strategy 3: Substring search (slower but more accurate)
            if not chunk_id:
                for stored_content, stored_id in content_to_chunk_id.items():
                    if len(stored_content) > 100 and stored_content[:80] in ctx_clean[:200]:
                        chunk_id = stored_id
                        break
            
            if chunk_id:
                reference_chunk_ids.append(chunk_id)
            else:
                # Fallback: create hash-based ID (should be rare now)
                import hashlib
                fallback_id = f"synth_chunk_{hashlib.md5(ctx[:50].encode()).hexdigest()[:8]}"
                reference_chunk_ids.append(fallback_id)
                logger.debug(f"Could not match context to chunk, using fallback: {fallback_id}")
        
        sample = {
            "query_id": f"synth_{i+1:03d}",
            "query": row.user_input,
            "reference_answer": row.reference,
            "reference_contexts": contexts,
            "reference_chunk_ids": reference_chunk_ids,  # Proper chunk IDs
        }
        samples.append(sample)
    
    logger.info(f"Generated {len(samples)} samples")
    return samples


def export_to_jsonl(
    samples: List[Dict[str, Any]],
    output_dir: str = "datasets",
    prefix: str = "synthetic",
) -> Dict[str, str]:
    """
    Exportiert generierte Samples zu JSONL-Dateien.
    
    Erstellt:
    - {prefix}_queries.jsonl
    - {prefix}_answers.jsonl
    - {prefix}_qrels_semantic.jsonl
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    queries_path = output_path / f"{prefix}_queries.jsonl"
    answers_path = output_path / f"{prefix}_answers.jsonl"
    qrels_path = output_path / f"{prefix}_qrels_semantic.jsonl"
    
    # Queries
    with open(queries_path, "w", encoding="utf-8") as f:
        for sample in samples:
            query_obj = {
                "query_id": sample["query_id"],
                "text": sample["query"],
                "query_type": "knowledge",
                "expected_source": "retrieval",
            }
            f.write(json.dumps(query_obj, ensure_ascii=False) + "\n")
    
    logger.info(f"Wrote {len(samples)} queries to {queries_path}")
    
    # Answers
    with open(answers_path, "w", encoding="utf-8") as f:
        for sample in samples:
            answer_obj = {
                "query_id": sample["query_id"],
                "answers": [sample["reference_answer"]],
                "explanation": "Synthetisch generiert von RAGAS",
            }
            f.write(json.dumps(answer_obj, ensure_ascii=False) + "\n")
    
    logger.info(f"Wrote {len(samples)} answers to {answers_path}")
    
    # Qrels (basierend auf reference_chunk_ids)
    qrels_count = 0
    with open(qrels_path, "w", encoding="utf-8") as f:
        for sample in samples:
            chunk_ids = sample.get("reference_chunk_ids", [])
            for chunk_id in chunk_ids:
                qrel_obj = {
                    "query_id": sample["query_id"],
                    "chunk_id": chunk_id,
                    "relevance": 3,
                }
                f.write(json.dumps(qrel_obj, ensure_ascii=False) + "\n")
                qrels_count += 1
    
    logger.info(f"Wrote {qrels_count} qrels to {qrels_path}")
    
    return {
        "queries": str(queries_path),
        "answers": str(answers_path),
        "qrels": str(qrels_path),
    }


@app.callback(invoke_without_command=True)
def generate(
    num_samples: int = typer.Option(10, help="Anzahl der zu generierenden Samples"),
    generator_model: str = typer.Option("qwen3:8b", help="LLM für Generierung"),
    embedding_model: str = typer.Option("qwen3-embedding:4b", help="Embedding Modell"),
    index_name: str = typer.Option("chunks_semantic_qwen3", help="OpenSearch Index"),
    output_prefix: str = typer.Option("synthetic", help="Prefix für Output-Dateien"),
):
    """
    Generiert synthetische Evaluation-Daten mit RAGAS.
    """
    logger.info("=" * 60)
    logger.info("SYNTHETIC DATA GENERATION")
    logger.info("=" * 60)
    
    # 1. Load chunks
    logger.info("\n1. Loading chunks from OpenSearch...")
    chunks = load_chunks_from_opensearch(index_name=index_name)
    
    if not chunks:
        logger.error("No chunks found!")
        raise typer.Exit(1)
    
    # 2. Convert to documents
    logger.info("\n2. Converting to LangChain documents...")
    documents = chunks_to_documents(chunks)
    
    # 3. Generate testset
    logger.info("\n3. Generating synthetic testset...")
    samples = generate_synthetic_testset(
        documents=documents,
        generator_model=generator_model,
        embedding_model=embedding_model,
        num_samples=num_samples,
    )
    
    # 4. Export
    logger.info("\n4. Exporting to JSONL files...")
    paths = export_to_jsonl(samples, prefix=output_prefix)
    
    logger.info("\n" + "=" * 60)
    logger.info("GENERATION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Queries: {paths['queries']}")
    logger.info(f"Answers: {paths['answers']}")
    logger.info(f"Qrels: {paths['qrels']}")
    
    # Print samples for review
    logger.info("\n📋 Sample Preview (first 2):")
    for sample in samples[:2]:
        print(f"\n[{sample['query_id']}]")
        print(f"Q: {sample['query'][:100]}...")
        print(f"A: {sample['reference_answer'][:100]}...")


if __name__ == "__main__":
    setup_logging()
    app()
