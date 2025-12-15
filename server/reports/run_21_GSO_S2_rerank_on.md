# Evaluation Report: GSO_S2_rerank_on

**Run ID:** 21
**Erstellt:** 2025-12-11 20:05:55
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
| **semantic_sim** | 0.8242 | [0.8004, 0.8481] | 16 |
| rouge_l_recall | 0.2927 | [0.2271, 0.3583] | 16 |
| content_f1 | 0.3205 | [0.2795, 0.3615] | 16 |
| bertscore_f1 | 0.7328 | [0.7234, 0.7422] | 16 |

## Faithfulness & Relevance (RAGAS)

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.8031 | [0.6912, 0.9151] | 16 |
| citation_precision | 0.4250 | [0.3184, 0.5316] | 16 |
| factual_consistency_score | 3.0625 | [2.9400, 3.1850] | 16 |
| **factual_consistency_normalized** | 0.5156 | [0.4850, 0.5463] | 16 |
| llm_answer_relevance | 0.6562 | [0.5390, 0.7735] | 16 |
| llm_context_relevance | 0.5312 | [0.4700, 0.5925] | 16 |
| llm_faithfulness | 0.6250 | [0.5154, 0.7346] | 16 |

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

*Report generiert am 2025-12-13 14:33:30*