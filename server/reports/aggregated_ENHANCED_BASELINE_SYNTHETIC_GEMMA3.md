# Aggregated Report: ENHANCED_BASELINE_SYNTHETIC_GEMMA3

**Repeats:** 3
**Runs:** ENHANCED_BASELINE_SYNTHETIC_GEMMA3_r1, ENHANCED_BASELINE_SYNTHETIC_GEMMA3_r2, ENHANCED_BASELINE_SYNTHETIC_GEMMA3_r3

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
| semantic_sim | 0.7926 | 0.0045 | [0.7875, 0.7978] | 3 |
| rouge_l_recall | 0.4706 | 0.0244 | [0.4429, 0.4982] | 3 |
| content_f1 | 0.2658 | 0.0119 | [0.2523, 0.2792] | 3 |
| bertscore_f1 | 0.7468 | 0.0061 | [0.7399, 0.7537] | 3 |

### Faithfulness & Relevance (RAGAS)

| Metrik | Mean | Std | 95% CI | N |
|--------|-----:|----:|--------|--:|
| citation_recall | 0.7581 | 0.0000 | [0.7581, 0.7581] | 3 |
| citation_precision | 0.2194 | 0.0000 | [0.2194, 0.2194] | 3 |
| factual_consistency_score | 3.0753 | 0.0186 | [3.0542, 3.0963] | 3 |
| factual_consistency_normalized | 0.5188 | 0.0047 | [0.5135, 0.5241] | 3 |
| llm_answer_relevance | 0.6801 | 0.0525 | [0.6207, 0.7395] | 3 |
| llm_context_relevance | 0.5081 | 0.0000 | [0.5081, 0.5081] | 3 |
| llm_faithfulness | 0.6022 | 0.0246 | [0.5743, 0.6300] | 3 |

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
| ENHANCED_BASELINE_SYNTHETIC_GEMMA3_r1 | 0.7581 | 0.5242 | 0.5806 | 0.7942 |
| ENHANCED_BASELINE_SYNTHETIC_GEMMA3_r2 | 0.7581 | 0.5161 | 0.6290 | 0.7876 |
| ENHANCED_BASELINE_SYNTHETIC_GEMMA3_r3 | 0.7581 | 0.5161 | 0.5968 | 0.7962 |

---

*Report generiert am 2025-12-17 01:03:14*