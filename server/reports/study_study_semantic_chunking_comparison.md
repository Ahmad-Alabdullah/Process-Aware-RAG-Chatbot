# Study Report: study_semantic_chunking_comparison

**Baseline:** OFAT_chunk_semantic_qwen3
**Varianten:** 1
**Primäre Metriken:** llm_faithfulness, llm_context_relevance, llm_answer_relevance

---

## Übersicht: Primäre Metriken

| Variante | llm_faithfulness | llm_context_relevance | llm_answer_relevance |
|----------|---:|---:|---:|
| **OFAT_chunk_semantic_qwen3** (Baseline) | 0.6111 | 0.5833 | 0.6111 |
| SENTENCE_SEMANTIC | 0.5556 (↓ -0.0556) | 0.5417 (↓ -0.0417) | 0.6111 (≈0) |

*Signifikanz: *** p<0.001, ** p<0.01, * p<0.05*

## Ranking nach llm_faithfulness

1. **OFAT_chunk_semantic_qwen3** (Baseline): 0.6111
2. **SENTENCE_SEMANTIC**: 0.5556

## Ranking nach llm_context_relevance

1. **OFAT_chunk_semantic_qwen3** (Baseline): 0.5833
2. **SENTENCE_SEMANTIC**: 0.5417

## Ranking nach llm_answer_relevance

1. **OFAT_chunk_semantic_qwen3** (Baseline): 0.6111
2. **SENTENCE_SEMANTIC**: 0.6111


---

## Detailvergleiche

### SENTENCE_SEMANTIC

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| llm_faithfulness | 0.6111 | 0.5556 | ↓ -0.0556 |  |
| llm_context_relevance | 0.5833 | 0.5417 | ↓ -0.0417 |  |
| llm_answer_relevance | 0.6111 | 0.6111 | ≈0 |  |
| factual_consistency_normalized | 0.5556 | 0.5139 | ↓ -0.0417 |  |
| semantic_sim | 0.8306 | 0.8386 | ↑ +0.0080 |  |


---

*Report generiert am 2025-12-13 14:07:33*