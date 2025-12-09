# Evaluation Report: BASELINE

**Run ID:** 1
**Erstellt:** 2025-12-08 19:45:09
**Dataset:** demo

---

## Konfiguration

```yaml
model: qwen3:8b
top_k: 5
use_rerank: False
prompt_style: baseline
retrieval_mode: hybrid
rrf_k: 60
```

## Retrieval-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| recall@3 | 0.5421 | [0.3854, 0.6989] | 18 |
| **recall@5** | 0.6597 | [0.5195, 0.7999] | 18 |
| recall@10 | 0.6597 | [0.5195, 0.7999] | 18 |
| mrr@3 | 0.8056 | [0.6510, 0.9601] | 18 |
| mrr@5 | 0.8194 | [0.6795, 0.9593] | 18 |
| mrr@10 | 0.8194 | [0.6795, 0.9593] | 18 |
| ndcg@3 | 0.6129 | [0.4457, 0.7800] | 18 |
| ndcg@5 | 0.6664 | [0.5256, 0.8072] | 18 |
| ndcg@10 | 0.6624 | [0.5190, 0.8057] | 18 |

## Generation-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| **semantic_sim** | 0.8449 | [0.8225, 0.8673] | 17 |
| rouge_l_recall | 0.2653 | [0.2233, 0.3072] | 17 |
| content_f1 | 0.3165 | [0.2805, 0.3526] | 17 |
| bertscore_f1 | 0.7398 | [0.7316, 0.7481] | 17 |

## Faithfulness-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.6515 | [0.5038, 0.7992] | 17 |
| citation_precision | 0.3647 | [0.2743, 0.4551] | 17 |
| factual_consistency_score | 3.0588 | [2.9435, 3.1741] | 17 |
| **factual_consistency_normalized** | 0.5147 | [0.4859, 0.5435] | 17 |

## H2 Gating-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| **h2_error_rate** | 0.0000 | [0.0000, 0.0000] | 0 |
| h2_structure_violation_rate | 0.0000 | [0.0000, 0.0000] | 0 |
| h2_hallucination_rate | 0.0000 | [0.0000, 0.0000] | 0 |
| h2_hint_adherence | 0.0000 | [0.0000, 0.0000] | 0 |
| h2_knowledge_score | 0.0000 | [0.0000, 0.0000] | 0 |
| h2_context_respected | 0.0000 | [0.0000, 0.0000] | 0 |
| h2_integration_score | 0.0000 | [0.0000, 0.0000] | 0 |
| h2_scope_violation_rate | 0.0000 | [0.0000, 0.0000] | 0 |
| gating_avg_gating_recall | 0.0000 | [0.0000, 0.0000] | 0 |
| gating_avg_gating_precision | 0.0000 | [0.0000, 0.0000] | 0 |

---

*Report generiert am 2025-12-08 21:36:35*