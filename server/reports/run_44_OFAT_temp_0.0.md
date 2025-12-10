# Evaluation Report: OFAT_temp_0.0

**Run ID:** 44
**Erstellt:** 2025-12-10 14:15:56
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
| **semantic_sim** | 0.8367 | [0.8146, 0.8588] | 18 |
| rouge_l_recall | 0.2583 | [0.2189, 0.2976] | 18 |
| content_f1 | 0.3104 | [0.2740, 0.3467] | 18 |
| bertscore_f1 | 0.7341 | [0.7241, 0.7441] | 18 |

## Faithfulness-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.6597 | [0.5195, 0.7999] | 18 |
| citation_precision | 0.3889 | [0.2914, 0.4864] | 18 |
| factual_consistency_score | 3.1111 | [2.8933, 3.3289] | 18 |
| **factual_consistency_normalized** | 0.5278 | [0.4733, 0.5822] | 18 |

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

*Report generiert am 2025-12-10 15:25:30*