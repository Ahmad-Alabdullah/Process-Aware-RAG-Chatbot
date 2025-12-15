# Aggregated Report: ENHANCED_BASELINE_SYNTHETIC

**Repeats:** 3
**Runs:** ENHANCED_BASELINE_SYNTHETIC_r1, ENHANCED_BASELINE_SYNTHETIC_r2, ENHANCED_BASELINE_SYNTHETIC_r3

---

## Aggregated Metrics (Mean ± Std)

### Retrieval-Metriken

| Metrik | Mean | Std | 95% CI | N |
|--------|-----:|----:|--------|--:|
| recall@3 | 0.8438 | 0.0000 | [0.8438, 0.8438] | 3 |
| recall@5 | 0.9062 | 0.0000 | [0.9062, 0.9062] | 3 |
| recall@10 | 0.9062 | 0.0000 | [0.9062, 0.9062] | 3 |
| mrr@3 | 0.8681 | 0.0000 | [0.8681, 0.8681] | 3 |
| mrr@5 | 0.8774 | 0.0000 | [0.8774, 0.8774] | 3 |
| mrr@10 | 0.8774 | 0.0000 | [0.8774, 0.8774] | 3 |
| ndcg@3 | 0.8117 | 0.0000 | [0.8117, 0.8117] | 3 |
| ndcg@5 | 0.8386 | 0.0000 | [0.8386, 0.8386] | 3 |
| ndcg@10 | 0.8386 | 0.0000 | [0.8386, 0.8386] | 3 |

### Generation-Metriken

| Metrik | Mean | Std | 95% CI | N |
|--------|-----:|----:|--------|--:|
| semantic_sim | 0.8477 | 0.0047 | [0.8424, 0.8530] | 3 |
| rouge_l_recall | 0.4990 | 0.0163 | [0.4806, 0.5174] | 3 |
| content_f1 | 0.3903 | 0.0144 | [0.3739, 0.4066] | 3 |
| bertscore_f1 | 0.7696 | 0.0048 | [0.7642, 0.7751] | 3 |

### Faithfulness & Relevance (RAGAS)

| Metrik | Mean | Std | 95% CI | N |
|--------|-----:|----:|--------|--:|
| citation_recall | 0.9062 | 0.0000 | [0.9062, 0.9062] | 3 |
| citation_precision | 0.2833 | 0.0000 | [0.2833, 0.2833] | 3 |
| factual_consistency_score | 3.1389 | 0.0789 | [3.0496, 3.2281] | 3 |
| factual_consistency_normalized | 0.5347 | 0.0197 | [0.5124, 0.5570] | 3 |
| llm_answer_relevance | 0.7222 | 0.0246 | [0.6944, 0.7501] | 3 |
| llm_context_relevance | 0.4740 | 0.0000 | [0.4740, 0.4740] | 3 |
| llm_faithfulness | 0.6128 | 0.0217 | [0.5883, 0.6374] | 3 |

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
| ENHANCED_BASELINE_SYNTHETIC_r1 | 0.9062 | 0.5260 | 0.6198 | 0.8501 |
| ENHANCED_BASELINE_SYNTHETIC_r2 | 0.9062 | 0.5573 | 0.5885 | 0.8423 |
| ENHANCED_BASELINE_SYNTHETIC_r3 | 0.9062 | 0.5208 | 0.6302 | 0.8507 |

---

*Report generiert am 2025-12-15 19:26:24*