# Evaluation Report: H2_GATING_ENABLED_r3

**Run ID:** 142
**Erstellt:** 2026-01-29 13:46:19
**Dataset:** demo_queries_process

---

## Konfiguration

```yaml
model: qwen2.5:7b-instruct
top_k: 5
use_rerank: False
prompt_style: cot
retrieval_mode: hybrid
rrf_k: 60
```

## Retrieval-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| recall@3 | 0.0000 | [0.0000, 0.0000] | 0 |
| **recall@5** | 0.0000 | [0.0000, 0.0000] | 0 |
| recall@10 | 0.0000 | [0.0000, 0.0000] | 0 |
| mrr@3 | 0.0000 | [0.0000, 0.0000] | 0 |
| mrr@5 | 0.0000 | [0.0000, 0.0000] | 0 |
| mrr@10 | 0.0000 | [0.0000, 0.0000] | 0 |
| ndcg@3 | 0.0000 | [0.0000, 0.0000] | 0 |
| ndcg@5 | 0.0000 | [0.0000, 0.0000] | 0 |
| ndcg@10 | 0.0000 | [0.0000, 0.0000] | 0 |

## Generation-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| **semantic_sim** | 0.0000 | [0.0000, 0.0000] | 0 |
| rouge_l_recall | 0.0000 | [0.0000, 0.0000] | 0 |
| content_f1 | 0.0000 | [0.0000, 0.0000] | 0 |
| bertscore_f1 | 0.0000 | [0.0000, 0.0000] | 0 |

## Faithfulness & Relevance (RAGAS)

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 1.0000 | [1.0000, 1.0000] | 10 |
| citation_precision | 0.6000 | [0.2799, 0.9201] | 10 |
| factual_consistency_score | 0.0000 | [0.0000, 0.0000] | 0 |
| **factual_consistency_normalized** | 0.0000 | [0.0000, 0.0000] | 0 |
| llm_answer_relevance | 0.5500 | [0.4847, 0.6153] | 10 |
| llm_context_relevance | 0.5000 | [0.5000, 0.5000] | 4 |
| llm_faithfulness | 0.0000 | [0.0000, 0.0000] | 0 |

## H2 Gating-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| **h2_error_rate** | 0.4250 | [0.3502, 0.4998] | 10 |
| llm_answer_relevance | 0.5500 | [0.4847, 0.6153] | 10 |

## H3 Grauzonen-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| **h3_appropriate_handling** | 0.0000 | [0.0000, 0.0000] | 0 |
| h3_speculation_detected | 0.0000 | [0.0000, 0.0000] | 0 |
| h3_uncertainty_expressed | 0.0000 | [0.0000, 0.0000] | 0 |
| h3_score | 0.0000 | [0.0000, 0.0000] | 0 |

---

*Report generiert am 2026-01-29 21:55:48*