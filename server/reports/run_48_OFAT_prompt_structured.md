# Evaluation Report: OFAT_prompt_structured

**Run ID:** 48
**Erstellt:** 2025-12-10 14:56:07
**Dataset:** demo

---

## Konfiguration

```yaml
model: qwen3:8b
top_k: 5
use_rerank: False
prompt_style: structured
retrieval_mode: hybrid
rrf_k: 60
```

## Retrieval-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| recall@3 | 0.4221 | [0.2452, 0.5991] | 18 |
| **recall@5** | 0.4851 | [0.3226, 0.6476] | 18 |
| recall@10 | 0.4851 | [0.3226, 0.6476] | 18 |
| mrr@3 | 0.8056 | [0.6510, 0.9601] | 18 |
| mrr@5 | 0.8194 | [0.6795, 0.9593] | 18 |
| mrr@10 | 0.8194 | [0.6795, 0.9593] | 18 |
| ndcg@3 | 0.5616 | [0.3949, 0.7283] | 18 |
| ndcg@5 | 0.5710 | [0.4214, 0.7205] | 18 |
| ndcg@10 | 0.5349 | [0.3802, 0.6896] | 18 |

## Generation-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| **semantic_sim** | 0.8448 | [0.8154, 0.8742] | 17 |
| rouge_l_recall | 0.2109 | [0.1741, 0.2476] | 17 |
| content_f1 | 0.2994 | [0.2675, 0.3312] | 17 |
| bertscore_f1 | 0.7477 | [0.7401, 0.7552] | 17 |

## Faithfulness-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.4901 | [0.3181, 0.6621] | 17 |
| citation_precision | 0.3647 | [0.2743, 0.4551] | 17 |
| factual_consistency_score | 3.0000 | [3.0000, 3.0000] | 17 |
| **factual_consistency_normalized** | 0.5000 | [0.5000, 0.5000] | 17 |

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

*Report generiert am 2025-12-10 16:03:24*