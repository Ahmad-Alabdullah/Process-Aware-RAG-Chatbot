# Evaluation Report: H1_BM25_ONLY_RERANK_r1

**Run ID:** 98
**Erstellt:** 2025-12-18 14:12:48
**Dataset:** demo

---

## Konfiguration

```yaml
model: qwen2.5:7b-instruct
top_k: 5
use_rerank: True
prompt_style: cot
retrieval_mode: bm25_only
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
| **semantic_sim** | 0.8471 | [0.8311, 0.8631] | 18 |
| rouge_l_recall | 0.2626 | [0.2101, 0.3150] | 18 |
| content_f1 | 0.3184 | [0.2765, 0.3604] | 18 |
| bertscore_f1 | 0.7451 | [0.7335, 0.7568] | 18 |

## Faithfulness & Relevance (RAGAS)

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.7631 | [0.6476, 0.8786] | 18 |
| citation_precision | 0.4333 | [0.3369, 0.5297] | 18 |
| factual_consistency_score | 3.0000 | [3.0000, 3.0000] | 18 |
| **factual_consistency_normalized** | 0.5000 | [0.5000, 0.5000] | 18 |
| llm_faithfulness | 0.5972 | [0.5166, 0.6778] | 18 |

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

*Report generiert am 2025-12-18 15:21:02*