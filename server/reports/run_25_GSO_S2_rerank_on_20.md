# Evaluation Report: GSO_S2_rerank_on_20

**Run ID:** 25
**Erstellt:** 2025-12-13 13:43:23
**Dataset:** demo

---

## Konfiguration

```yaml
model: qwen3:8b
top_k: 5
use_rerank: True
prompt_style: baseline
retrieval_mode: hybrid
rrf_k: 60
```

## Retrieval-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| recall@3 | 0.6645 | [0.5261, 0.8029] | 18 |
| **recall@5** | 0.7631 | [0.6476, 0.8786] | 18 |
| recall@10 | 0.7631 | [0.6476, 0.8786] | 18 |
| mrr@3 | 0.9630 | [0.8904, 1.0356] | 18 |
| mrr@5 | 0.9630 | [0.8904, 1.0356] | 18 |
| mrr@10 | 0.9630 | [0.8904, 1.0356] | 18 |
| ndcg@3 | 0.7629 | [0.6416, 0.8842] | 18 |
| ndcg@5 | 0.7822 | [0.6691, 0.8952] | 18 |
| ndcg@10 | 0.7707 | [0.6567, 0.8848] | 18 |

## Generation-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| **semantic_sim** | 0.8316 | [0.8081, 0.8550] | 17 |
| rouge_l_recall | 0.2776 | [0.2263, 0.3289] | 17 |
| content_f1 | 0.3204 | [0.2729, 0.3678] | 17 |
| bertscore_f1 | 0.7350 | [0.7233, 0.7467] | 17 |

## Faithfulness & Relevance (RAGAS)

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.7727 | [0.6518, 0.8936] | 17 |
| citation_precision | 0.4235 | [0.3233, 0.5237] | 17 |
| factual_consistency_score | 3.2941 | [2.9680, 3.6202] | 17 |
| **factual_consistency_normalized** | 0.5735 | [0.4920, 0.6551] | 17 |
| llm_answer_relevance | 0.6471 | [0.5354, 0.7587] | 17 |
| llm_context_relevance | 0.5294 | [0.4718, 0.5871] | 17 |
| llm_faithfulness | 0.6029 | [0.5084, 0.6974] | 17 |

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

*Report generiert am 2025-12-13 14:57:34*