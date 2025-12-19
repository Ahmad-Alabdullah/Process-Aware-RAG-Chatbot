# Aggregated Report: H1_HYBRID_DEMO

**Repeats:** 3
**Runs:** H1_HYBRID_DEMO_r1, H1_HYBRID_DEMO_r2, H1_HYBRID_DEMO_r3

---

## Aggregated Metrics (Mean ± Std)

### Retrieval-Metriken

| Metrik | Mean | Std | 95% CI | N |
|--------|-----:|----:|--------|--:|
| recall@3 | 0.6584 | 0.0000 | [0.6584, 0.6584] | 3 |
| recall@5 | 0.7330 | 0.0000 | [0.7330, 0.7330] | 3 |
| recall@10 | 0.7330 | 0.0000 | [0.7330, 0.7330] | 3 |
| mrr@3 | 0.9167 | 0.0000 | [0.9167, 0.9167] | 3 |
| mrr@5 | 0.9306 | 0.0000 | [0.9306, 0.9306] | 3 |
| mrr@10 | 0.9306 | 0.0000 | [0.9306, 0.9306] | 3 |
| ndcg@3 | 0.7706 | 0.0000 | [0.7706, 0.7706] | 3 |
| ndcg@5 | 0.7887 | 0.0000 | [0.7887, 0.7887] | 3 |
| ndcg@10 | 0.7833 | 0.0000 | [0.7833, 0.7833] | 3 |

### Generation-Metriken

| Metrik | Mean | Std | 95% CI | N |
|--------|-----:|----:|--------|--:|
| semantic_sim | 0.8465 | 0.0010 | [0.8453, 0.8477] | 3 |
| rouge_l_recall | 0.2660 | 0.0096 | [0.2551, 0.2769] | 3 |
| content_f1 | 0.3226 | 0.0098 | [0.3115, 0.3338] | 3 |
| bertscore_f1 | 0.7471 | 0.0027 | [0.7441, 0.7502] | 3 |

### Faithfulness & Relevance (RAGAS)

| Metrik | Mean | Std | 95% CI | N |
|--------|-----:|----:|--------|--:|
| citation_recall | 0.7330 | 0.0000 | [0.7330, 0.7330] | 3 |
| citation_precision | 0.3889 | 0.0000 | [0.3889, 0.3889] | 3 |
| factual_consistency_score | 3.0556 | 0.0556 | [2.9927, 3.1184] | 3 |
| factual_consistency_normalized | 0.5139 | 0.0139 | [0.4982, 0.5296] | 3 |
| llm_faithfulness | 0.6250 | 0.0278 | [0.5936, 0.6564] | 3 |

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
| H1_HYBRID_DEMO_r1 | 0.7330 | 0.5000 | 0.6250 | 0.8453 |
| H1_HYBRID_DEMO_r2 | 0.7330 | 0.5278 | 0.5972 | 0.8469 |
| H1_HYBRID_DEMO_r3 | 0.7330 | 0.5139 | 0.6528 | 0.8473 |

---

*Report generiert am 2025-12-18 13:49:04*