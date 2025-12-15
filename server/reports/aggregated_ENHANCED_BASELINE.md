# Aggregated Report: ENHANCED_BASELINE

**Repeats:** 3
**Runs:** ENHANCED_BASELINE_r1, ENHANCED_BASELINE_r2, ENHANCED_BASELINE_r3

---

## Aggregated Metrics (Mean ± Std)

### Retrieval-Metriken

| Metrik | Mean | Std | 95% CI | N |
|--------|-----:|----:|--------|--:|
| recall@3 | 0.6542 | 0.0000 | [0.6542, 0.6542] | 3 |
| recall@5 | 0.7612 | 0.0000 | [0.7612, 0.7612] | 3 |
| recall@10 | 0.7612 | 0.0000 | [0.7612, 0.7612] | 3 |
| mrr@3 | 0.9074 | 0.0000 | [0.9074, 0.9074] | 3 |
| mrr@5 | 0.9074 | 0.0000 | [0.9074, 0.9074] | 3 |
| mrr@10 | 0.9074 | 0.0000 | [0.9074, 0.9074] | 3 |
| ndcg@3 | 0.7324 | 0.0000 | [0.7324, 0.7324] | 3 |
| ndcg@5 | 0.7700 | 0.0000 | [0.7700, 0.7700] | 3 |
| ndcg@10 | 0.7682 | 0.0000 | [0.7682, 0.7682] | 3 |

### Generation-Metriken

| Metrik | Mean | Std | 95% CI | N |
|--------|-----:|----:|--------|--:|
| semantic_sim | 0.8472 | 0.0108 | [0.8350, 0.8594] | 3 |
| rouge_l_recall | 0.2686 | 0.0026 | [0.2657, 0.2715] | 3 |
| content_f1 | 0.3182 | 0.0105 | [0.3062, 0.3301] | 3 |
| bertscore_f1 | 0.7490 | 0.0039 | [0.7446, 0.7534] | 3 |

### Faithfulness & Relevance (RAGAS)

| Metrik | Mean | Std | 95% CI | N |
|--------|-----:|----:|--------|--:|
| citation_recall | 0.7612 | 0.0000 | [0.7612, 0.7612] | 3 |
| citation_precision | 0.4000 | 0.0000 | [0.4000, 0.4000] | 3 |
| factual_consistency_score | 3.0741 | 0.0642 | [3.0015, 3.1467] | 3 |
| factual_consistency_normalized | 0.5185 | 0.0160 | [0.5004, 0.5367] | 3 |
| llm_answer_relevance | 0.6435 | 0.0212 | [0.6195, 0.6675] | 3 |
| llm_context_relevance | 0.5833 | 0.0000 | [0.5833, 0.5833] | 3 |
| llm_faithfulness | 0.6435 | 0.0289 | [0.6108, 0.6762] | 3 |

### H2 Gating-Metriken

| Metrik | Mean | Std | 95% CI | N |
|--------|-----:|----:|--------|--:|
| h2_error_rate | 0.0000 | 0.0000 | [0.0000, 0.0000] | 3 |
| h2_structure_violation_rate | 0.0000 | 0.0000 | [0.0000, 0.0000] | 3 |
| h2_hallucination_rate | 0.0000 | 0.0000 | [0.0000, 0.0000] | 3 |
| h2_hint_adherence | 0.0000 | 0.0000 | [0.0000, 0.0000] | 3 |
| h2_knowledge_score | 0.0000 | 0.0000 | [0.0000, 0.0000] | 3 |
| h2_context_respected | 0.0000 | 0.0000 | [0.0000, 0.0000] | 3 |
| h2_integration_score | 0.0000 | 0.0000 | [0.0000, 0.0000] | 3 |
| h2_scope_violation_rate | 0.0000 | 0.0000 | [0.0000, 0.0000] | 3 |
| gating_avg_gating_recall | 0.0000 | 0.0000 | [0.0000, 0.0000] | 3 |
| gating_avg_gating_precision | 0.0000 | 0.0000 | [0.0000, 0.0000] | 3 |

---

## Individual Run Values

| Run | recall@5 | factual_consistency_normalized | llm_faithfulness | semantic_sim |
|-----|----:|----:|----:|----:|
| ENHANCED_BASELINE_r1 | 0.7612 | 0.5278 | 0.6111 | 0.8478 |
| ENHANCED_BASELINE_r2 | 0.7612 | 0.5000 | 0.6667 | 0.8362 |
| ENHANCED_BASELINE_r3 | 0.7612 | 0.5278 | 0.6528 | 0.8576 |

---

*Report generiert am 2025-12-14 13:00:02*