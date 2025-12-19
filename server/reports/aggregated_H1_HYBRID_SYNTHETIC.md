# Aggregated Report: H1_HYBRID_SYNTHETIC

**Repeats:** 3
**Runs:** H1_HYBRID_SYNTHETIC_r1, H1_HYBRID_SYNTHETIC_r2, H1_HYBRID_SYNTHETIC_r3

---

## Aggregated Metrics (Mean ± Std)

### Retrieval-Metriken

| Metrik | Mean | Std | 95% CI | N |
|--------|-----:|----:|--------|--:|
| recall@3 | 0.6452 | 0.0000 | [0.6452, 0.6452] | 3 |
| recall@5 | 0.7581 | 0.0000 | [0.7581, 0.7581] | 3 |
| recall@10 | 0.7581 | 0.0000 | [0.7581, 0.7581] | 3 |
| mrr@3 | 0.7688 | 0.0000 | [0.7688, 0.7688] | 3 |
| mrr@5 | 0.7849 | 0.0000 | [0.7849, 0.7849] | 3 |
| mrr@10 | 0.7849 | 0.0000 | [0.7849, 0.7849] | 3 |
| ndcg@3 | 0.6188 | 0.0000 | [0.6188, 0.6188] | 3 |
| ndcg@5 | 0.6727 | 0.0000 | [0.6727, 0.6727] | 3 |
| ndcg@10 | 0.6727 | 0.0000 | [0.6727, 0.6727] | 3 |

### Generation-Metriken

| Metrik | Mean | Std | 95% CI | N |
|--------|-----:|----:|--------|--:|
| semantic_sim | 0.7905 | 0.0109 | [0.7782, 0.8028] | 3 |
| rouge_l_recall | 0.4913 | 0.0053 | [0.4853, 0.4974] | 3 |
| content_f1 | 0.2822 | 0.0211 | [0.2583, 0.3061] | 3 |
| bertscore_f1 | 0.7529 | 0.0041 | [0.7483, 0.7575] | 3 |

### Faithfulness & Relevance (RAGAS)

| Metrik | Mean | Std | 95% CI | N |
|--------|-----:|----:|--------|--:|
| citation_recall | 0.7581 | 0.0000 | [0.7581, 0.7581] | 3 |
| citation_precision | 0.2194 | 0.0000 | [0.2194, 0.2194] | 3 |
| factual_consistency_score | 3.0323 | 0.0323 | [2.9958, 3.0688] | 3 |
| factual_consistency_normalized | 0.5081 | 0.0081 | [0.4989, 0.5172] | 3 |
| llm_answer_relevance | 0.5941 | 0.0203 | [0.5711, 0.6171] | 3 |
| llm_context_relevance | 0.5081 | 0.0000 | [0.5081, 0.5081] | 3 |
| llm_faithfulness | 0.5860 | 0.0093 | [0.5755, 0.5966] | 3 |

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
| H1_HYBRID_SYNTHETIC_r1 | 0.7581 | 0.5000 | 0.5806 | 0.7851 |
| H1_HYBRID_SYNTHETIC_r2 | 0.7581 | 0.5081 | 0.5806 | 0.8030 |
| H1_HYBRID_SYNTHETIC_r3 | 0.7581 | 0.5161 | 0.5968 | 0.7834 |

---

*Report generiert am 2025-12-18 16:35:44*