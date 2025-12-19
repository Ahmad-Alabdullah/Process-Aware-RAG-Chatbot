# Evaluation Report: H1_VECTOR_ONLY_RERANK_r2

**Run ID:** 93
**Erstellt:** 2025-12-18 13:29:26
**Dataset:** demo

---

## Konfiguration

```yaml
model: qwen2.5:7b-instruct
top_k: 5
use_rerank: True
prompt_style: cot
retrieval_mode: vector_only
rrf_k: 60
```

## Retrieval-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| recall@3 | 0.6565 | [0.5125, 0.8006] | 18 |
| **recall@5** | 0.7631 | [0.6476, 0.8786] | 18 |
| recall@10 | 0.7631 | [0.6476, 0.8786] | 18 |
| mrr@3 | 0.9630 | [0.8904, 1.0356] | 18 |
| mrr@5 | 0.9630 | [0.8904, 1.0356] | 18 |
| mrr@10 | 0.9630 | [0.8904, 1.0356] | 18 |
| ndcg@3 | 0.7549 | [0.6277, 0.8820] | 18 |
| ndcg@5 | 0.7813 | [0.6674, 0.8951] | 18 |
| ndcg@10 | 0.7699 | [0.6552, 0.8847] | 18 |

## Generation-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| **semantic_sim** | 0.8454 | [0.8250, 0.8658] | 18 |
| rouge_l_recall | 0.2755 | [0.2185, 0.3326] | 18 |
| content_f1 | 0.3111 | [0.2731, 0.3491] | 18 |
| bertscore_f1 | 0.7449 | [0.7342, 0.7556] | 18 |

## Faithfulness & Relevance (RAGAS)

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.7631 | [0.6476, 0.8786] | 18 |
| citation_precision | 0.4333 | [0.3369, 0.5297] | 18 |
| factual_consistency_score | 3.1111 | [2.9617, 3.2605] | 18 |
| **factual_consistency_normalized** | 0.5278 | [0.4904, 0.5651] | 18 |
| llm_faithfulness | 0.6389 | [0.5484, 0.7294] | 18 |

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

*Report generiert am 2025-12-18 14:39:27*