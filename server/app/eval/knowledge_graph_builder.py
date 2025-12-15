"""
Custom Knowledge Graph Builder for RAGAS Testset Generation.

Bypasses unreliable RAGAS default_transforms by building a knowledge graph
with LLM-extracted properties and all relationships required by synthesizers.

SYNTHESIZER REQUIREMENTS:
- SingleHopSpecificQuerySynthesizer: nodes with 'entities' or 'keyphrases' property
- MultiHopSpecificQuerySynthesizer: 'entities_overlap' relationships with 'overlapped_items' property
- MultiHopAbstractQuerySynthesizer: 'summary_similarity' property on relationships + 'themes' on nodes
"""

import asyncio
from typing import List, Dict, Any, Tuple, Set
from uuid import uuid4

import numpy as np
from langchain_core.documents import Document

from ragas.testset.graph import KnowledgeGraph, Node, NodeType, Relationship

from app.core.clients import get_logger

logger = get_logger(__name__)


# =============================================================================
# LLM PROPERTY EXTRACTION
# =============================================================================

PROPERTY_EXTRACTION_PROMPT = """Analysiere den folgenden deutschen Text und extrahiere strukturierte Informationen.

TEXT:
{text}

Antworte NUR im folgenden JSON-Format (keine Erklärungen, keine ```json Blöcke):
{{
    "title": "Kurzer beschreibender Titel (max 10 Worte)",
    "headlines": ["Überschrift 1", "Überschrift 2"],
    "keyphrases": ["Schlüsselbegriff 1", "Schlüsselbegriff 2", "Schlüsselbegriff 3"],
    "entities": ["Entität 1", "Entität 2", "Entität 3", "Entität 4", "Entität 5"],
    "summary": "1-2 Sätze Zusammenfassung des Inhalts",
    "themes": ["Thema 1", "Thema 2"]
}}

WICHTIG:
- Entitäten sind spezifische Begriffe: Gesetze (§ 1 BEEG), Formulare, Anträge, Institutionen, Personen, Fristen, Beträge
- keyphrases sind allgemeinere Schlüsselbegriffe aus dem Text
- themes sind übergeordnete Themengebiete (z.B. "Elterngeld", "Arbeitsrecht", "Antragstellung")
- Falls keine Überschriften im Text sind, erstelle 1-2 passende basierend auf dem Inhalt
- Extrahiere mindestens 3 entities und 2 themes wenn möglich"""


async def extract_node_properties(
    node: Node,
    llm,
    max_content_length: int = 3000,
) -> Dict[str, Any]:
    """
    Extract properties from a node using LLM.
    
    Args:
        node: The node to extract properties from
        llm: RAGAS-wrapped LLM (LangchainLLMWrapper)
        max_content_length: Max characters to send to LLM
        
    Returns:
        Dict with title, headlines, keyphrases, entities, summary, themes
    """
    import json
    
    content = node.properties.get("page_content", "")[:max_content_length]
    
    if not content.strip():
        return _get_empty_properties()
    
    prompt = PROPERTY_EXTRACTION_PROMPT.format(text=content)
    
    try:
        # Use the underlying langchain LLM
        response = await llm.langchain_llm.ainvoke(prompt)
        
        # Parse JSON from response
        response_text = str(response)
        
        # Try to extract JSON from response - handle various formats
        json_str = _extract_json(response_text)
        
        if json_str:
            properties = json.loads(json_str)
            return _normalize_properties(properties, content)
            
    except Exception as e:
        logger.warning(f"Property extraction failed for node: {e}")
    
    # Fallback: generate basic properties from content
    return _get_fallback_properties(content)


def _extract_json(text: str) -> str:
    """Extract JSON from LLM response, handling various formats."""
    # Remove thinking tags if present
    if "</think>" in text:
        text = text.split("</think>")[-1]
    
    # Find JSON object
    start_idx = text.find("{")
    end_idx = text.rfind("}") + 1
    
    if start_idx >= 0 and end_idx > start_idx:
        return text[start_idx:end_idx]
    return ""


def _get_empty_properties() -> Dict[str, Any]:
    """Return empty properties dict."""
    return {
        "title": "Leerer Inhalt",
        "headlines": [],
        "keyphrases": [],
        "entities": [],
        "summary": "",
        "themes": [],
    }


def _normalize_properties(props: Dict[str, Any], content: str) -> Dict[str, Any]:
    """Normalize and validate extracted properties."""
    # Ensure all lists are actually lists
    headlines = props.get("headlines", [])
    keyphrases = props.get("keyphrases", [])
    entities = props.get("entities", [])
    themes = props.get("themes", [])
    
    if isinstance(headlines, str):
        headlines = [headlines]
    if isinstance(keyphrases, str):
        keyphrases = [keyphrases]
    if isinstance(entities, str):
        entities = [entities]
    if isinstance(themes, str):
        themes = [themes]
    
    # Ensure minimum content for entities and themes (critical for synthesizers)
    if not entities:
        # Extract simple entities from content (words > 4 chars that look like terms)
        words = content.split()[:20]
        entities = [w for w in words if len(w) > 5 and w[0].isupper()][:3]
    
    if not themes:
        # Use keyphrases as themes fallback
        themes = keyphrases[:2] if keyphrases else ["Allgemein"]
    
    return {
        "title": props.get("title", content[:50]),
        "headlines": headlines if headlines else [content[:30]],
        "keyphrases": keyphrases,
        "entities": entities,
        "summary": props.get("summary", content[:200]),
        "themes": themes,
    }


def _get_fallback_properties(content: str) -> Dict[str, Any]:
    """Generate fallback properties from content."""
    # Extract capitalized words as pseudo-entities
    words = content.split()
    entities = list(set(w.strip(".,;:()") for w in words if len(w) > 4 and w[0].isupper()))[:5]
    
    return {
        "title": content[:50] + "..." if len(content) > 50 else content,
        "headlines": [content[:40]],
        "keyphrases": [],
        "entities": entities if entities else ["Dokument"],
        "summary": content[:200],
        "themes": ["Allgemein"],
    }


async def extract_properties_batch(
    nodes: List[Node],
    llm,
    batch_size: int = 5,
) -> List[Node]:
    """
    Extract properties for all nodes with rate limiting.
    
    Args:
        nodes: List of nodes to process
        llm: RAGAS-wrapped LLM
        batch_size: Number of concurrent requests
        
    Returns:
        List of nodes with updated properties
    """
    logger.info(f"Extracting properties for {len(nodes)} nodes...")
    
    semaphore = asyncio.Semaphore(batch_size)
    processed = 0
    
    async def process_node(node: Node, idx: int) -> Node:
        nonlocal processed
        async with semaphore:
            properties = await extract_node_properties(node, llm)
            node.properties.update(properties)
            processed += 1
            if processed % 20 == 0:
                logger.info(f"  Progress: {processed}/{len(nodes)} nodes processed")
            return node
    
    tasks = [process_node(node, i) for i, node in enumerate(nodes)]
    updated_nodes = await asyncio.gather(*tasks)
    
    logger.info(f"Property extraction complete for {len(updated_nodes)} nodes")
    return list(updated_nodes)


# =============================================================================
# EMBEDDING COMPUTATION
# =============================================================================

async def compute_node_embeddings(
    nodes: List[Node],
    embedding_model,
    property_name: str = "embedding",
) -> List[Node]:
    """
    Compute embeddings for all nodes.
    
    Args:
        nodes: List of nodes
        embedding_model: RAGAS-wrapped embedding model
        property_name: Name of the property to store embedding
        
    Returns:
        Nodes with embedding property added
    """
    logger.info(f"Computing embeddings for {len(nodes)} nodes...")
    
    # Collect texts to embed
    texts = []
    for node in nodes:
        content = node.properties.get("page_content", "")
        summary = node.properties.get("summary", "")
        # Combine content and summary for richer embedding
        combined = f"{content}\n\n{summary}" if summary else content
        texts.append(combined)
    
    # Batch embed using the underlying langchain embeddings
    embeddings = await embedding_model.embeddings.aembed_documents(texts)
    
    # Attach embeddings to nodes
    for node, embedding in zip(nodes, embeddings):
        node.properties[property_name] = embedding
    
    logger.info(f"Embeddings computed for {len(nodes)} nodes")
    return nodes


# =============================================================================
# RELATIONSHIP BUILDING
# =============================================================================

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a_arr = np.array(a)
    b_arr = np.array(b)
    norm_product = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    if norm_product == 0:
        return 0.0
    return float(np.dot(a_arr, b_arr) / norm_product)


def build_similarity_relationships(
    nodes: List[Node],
    similarity_threshold: float = 0.7,
    embedding_property: str = "embedding",
) -> List[Relationship]:
    """
    Build relationships between nodes based on embedding similarity.
    
    Adds both 'similarity' and 'summary_similarity' properties as required
    by MultiHopAbstractQuerySynthesizer.
    
    Args:
        nodes: List of nodes with embeddings
        similarity_threshold: Minimum cosine similarity for edge creation
        embedding_property: Name of embedding property
        
    Returns:
        List of Relationship objects
    """
    logger.info(f"Building similarity relationships for {len(nodes)} nodes (threshold={similarity_threshold})...")
    
    relationships = []
    
    for i, node_a in enumerate(nodes):
        emb_a = node_a.properties.get(embedding_property)
        if emb_a is None:
            continue
            
        doc_id_a = node_a.properties.get("document_metadata", {}).get("document_id")
        
        for j, node_b in enumerate(nodes):
            if i >= j:  # Skip self and already processed pairs
                continue
                
            emb_b = node_b.properties.get(embedding_property)
            if emb_b is None:
                continue
            
            # Compute similarity
            similarity = cosine_similarity(emb_a, emb_b)
            
            if similarity >= similarity_threshold:
                # Check if same document
                doc_id_b = node_b.properties.get("document_metadata", {}).get("document_id")
                rel_type = "cosine_similarity"  # Standard type for similarity
                
                relationship = Relationship(
                    source=node_a,
                    target=node_b,
                    type=rel_type,
                    properties={
                        "similarity": similarity,
                        # Required by MultiHopAbstractQuerySynthesizer:
                        "summary_similarity": similarity,
                    },
                )
                relationships.append(relationship)
    
    logger.info(f"Built {len(relationships)} similarity relationships")
    return relationships


def build_entity_overlap_relationships(
    nodes: List[Node],
    min_overlap: int = 1,
) -> List[Relationship]:
    """
    Build relationships based on overlapping entities between nodes.
    
    Required by MultiHopSpecificQuerySynthesizer which looks for
    'entities_overlap' relationship type with 'overlapped_items' property.
    
    Args:
        nodes: List of nodes with 'entities' property
        min_overlap: Minimum number of overlapping entities for edge creation
        
    Returns:
        List of Relationship objects with type 'entities_overlap'
    """
    logger.info(f"Building entity overlap relationships for {len(nodes)} nodes...")
    
    relationships = []
    
    for i, node_a in enumerate(nodes):
        entities_a = set(e.lower().strip() for e in node_a.properties.get("entities", []) if e)
        if not entities_a:
            continue
            
        for j, node_b in enumerate(nodes):
            if i >= j:  # Skip self and already processed pairs
                continue
                
            entities_b = set(e.lower().strip() for e in node_b.properties.get("entities", []) if e)
            if not entities_b:
                continue
            
            # Find overlapping entities
            overlap = entities_a.intersection(entities_b)
            
            if len(overlap) >= min_overlap:
                relationship = Relationship(
                    source=node_a,
                    target=node_b,
                    type="entities_overlap",  # Required by MultiHopSpecificQuerySynthesizer
                    properties={
                        "overlapped_items": list(overlap),  # Required property
                        "overlap_count": len(overlap),
                    },
                )
                relationships.append(relationship)
    
    logger.info(f"Built {len(relationships)} entity overlap relationships")
    return relationships


def build_keyphrase_overlap_relationships(
    nodes: List[Node],
    min_overlap: int = 1,
) -> List[Relationship]:
    """
    Build relationships based on overlapping keyphrases between nodes.
    
    Alternative relationship type for synthesizers.
    
    Args:
        nodes: List of nodes with 'keyphrases' property
        min_overlap: Minimum number of overlapping keyphrases
        
    Returns:
        List of Relationship objects
    """
    logger.info(f"Building keyphrase overlap relationships for {len(nodes)} nodes...")
    
    relationships = []
    
    for i, node_a in enumerate(nodes):
        keyphrases_a = set(k.lower().strip() for k in node_a.properties.get("keyphrases", []) if k)
        if not keyphrases_a:
            continue
            
        for j, node_b in enumerate(nodes):
            if i >= j:
                continue
                
            keyphrases_b = set(k.lower().strip() for k in node_b.properties.get("keyphrases", []) if k)
            if not keyphrases_b:
                continue
            
            overlap = keyphrases_a.intersection(keyphrases_b)
            
            if len(overlap) >= min_overlap:
                relationship = Relationship(
                    source=node_a,
                    target=node_b,
                    type="keyphrases_overlap",
                    properties={
                        "overlapped_items": list(overlap),
                        "overlap_count": len(overlap),
                    },
                )
                relationships.append(relationship)
    
    logger.info(f"Built {len(relationships)} keyphrase overlap relationships")
    return relationships


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def documents_to_nodes(documents: List[Document]) -> List[Node]:
    """Convert LangChain Documents to RAGAS Nodes."""
    nodes = []
    for doc in documents:
        node = Node(
            id=uuid4(),
            type=NodeType.DOCUMENT,
            properties={
                "page_content": doc.page_content,
                "document_metadata": doc.metadata,
            },
        )
        nodes.append(node)
    return nodes


async def build_knowledge_graph_async(
    documents: List[Document],
    llm,
    embedding_model,
    similarity_threshold: float = 0.7,
) -> KnowledgeGraph:
    """
    Build a knowledge graph from documents with LLM-extracted properties
    and all relationships required by RAGAS synthesizers.
    
    Args:
        documents: List of LangChain Documents
        llm: RAGAS-wrapped LLM (LangchainLLMWrapper)
        embedding_model: RAGAS-wrapped embeddings (LangchainEmbeddingsWrapper)
        similarity_threshold: Cosine similarity threshold for relationships
        
    Returns:
        KnowledgeGraph ready for RAGAS TestsetGenerator
    """
    logger.info(f"Building knowledge graph from {len(documents)} documents...")
    
    # Phase 1: Create nodes
    nodes = documents_to_nodes(documents)
    logger.info(f"Phase 1: Created {len(nodes)} nodes")
    
    # Phase 2: Extract properties using LLM
    # This extracts: title, headlines, keyphrases, entities, summary, themes
    logger.info("Phase 2: Extracting properties with LLM...")
    nodes = await extract_properties_batch(nodes, llm)
    
    # Log extraction stats
    nodes_with_entities = sum(1 for n in nodes if n.properties.get("entities"))
    nodes_with_themes = sum(1 for n in nodes if n.properties.get("themes"))
    logger.info(f"  Nodes with entities: {nodes_with_entities}/{len(nodes)}")
    logger.info(f"  Nodes with themes: {nodes_with_themes}/{len(nodes)}")
    
    # Phase 3: Compute embeddings
    logger.info("Phase 3: Computing embeddings...")
    nodes = await compute_node_embeddings(nodes, embedding_model)
    
    # Phase 4: Build all relationship types
    logger.info("Phase 4: Building relationships...")
    
    # 4a. Similarity-based relationships (for MultiHopAbstractQuerySynthesizer)
    similarity_rels = build_similarity_relationships(nodes, similarity_threshold)
    
    # 4b. Entity overlap relationships (for MultiHopSpecificQuerySynthesizer)
    entity_rels = build_entity_overlap_relationships(nodes, min_overlap=1)
    
    # 4c. Keyphrase overlap relationships (backup/alternative)
    keyphrase_rels = build_keyphrase_overlap_relationships(nodes, min_overlap=1)
    
    # Combine all relationships
    all_relationships = similarity_rels + entity_rels + keyphrase_rels
    
    # Phase 5: Create KnowledgeGraph
    kg = KnowledgeGraph(nodes=nodes, relationships=all_relationships)
    
    logger.info("=" * 60)
    logger.info("KNOWLEDGE GRAPH COMPLETE")
    logger.info("=" * 60)
    logger.info(f"  Total nodes: {len(kg.nodes)}")
    logger.info(f"  Total relationships: {len(kg.relationships)}")
    logger.info(f"    - Similarity (summary_similarity): {len(similarity_rels)}")
    logger.info(f"    - Entity overlap: {len(entity_rels)}")
    logger.info(f"    - Keyphrase overlap: {len(keyphrase_rels)}")
    
    return kg


def build_knowledge_graph(
    documents: List[Document],
    llm,
    embedding_model,
    similarity_threshold: float = 0.7,
) -> KnowledgeGraph:
    """
    Synchronous wrapper for build_knowledge_graph_async.
    """
    return asyncio.run(
        build_knowledge_graph_async(
            documents=documents,
            llm=llm,
            embedding_model=embedding_model,
            similarity_threshold=similarity_threshold,
        )
    )
