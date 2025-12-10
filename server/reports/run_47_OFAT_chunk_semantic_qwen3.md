# Evaluation Report: OFAT_chunk_semantic_qwen3

**Run ID:** 47
**Erstellt:** 2025-12-10 14:45:10
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
| recall@3 | 0.4486 | [0.2791, 0.6180] | 18 |
| **recall@5** | 0.4991 | [0.3403, 0.6579] | 18 |
| recall@10 | 0.4991 | [0.3403, 0.6579] | 18 |
| mrr@3 | 0.9074 | [0.7801, 1.0347] | 18 |
| mrr@5 | 0.9074 | [0.7801, 1.0347] | 18 |
| mrr@10 | 0.9074 | [0.7801, 1.0347] | 18 |
| ndcg@3 | 0.6415 | [0.4963, 0.7868] | 18 |
| ndcg@5 | 0.6170 | [0.4773, 0.7566] | 18 |
| ndcg@10 | 0.5765 | [0.4312, 0.7218] | 18 |

## Generation-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| **semantic_sim** | 0.8291 | [0.8096, 0.8486] | 18 |
| rouge_l_recall | 0.2914 | [0.2245, 0.3583] | 18 |
| content_f1 | 0.3184 | [0.2743, 0.3624] | 18 |
| bertscore_f1 | 0.7316 | [0.7222, 0.7409] | 18 |

## Faithfulness-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.4991 | [0.3403, 0.6579] | 18 |
| citation_precision | 0.4000 | [0.2949, 0.5051] | 18 |
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

*Report generiert am 2025-12-10 15:56:07*