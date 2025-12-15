# Evaluation Report: GSO_S5_hyde_r2

**Run ID:** 38
**Erstellt:** 2025-12-14 12:52:19
**Dataset:** demo

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
| recall@3 | 0.5987 | [0.4441, 0.7532] | 18 |
| **recall@5** | 0.7122 | [0.5686, 0.8557] | 18 |
| recall@10 | 0.7122 | [0.5686, 0.8557] | 18 |
| mrr@3 | 0.8333 | [0.6961, 0.9706] | 18 |
| mrr@5 | 0.8333 | [0.6961, 0.9706] | 18 |
| mrr@10 | 0.8333 | [0.6961, 0.9706] | 18 |
| ndcg@3 | 0.6636 | [0.5083, 0.8189] | 18 |
| ndcg@5 | 0.7083 | [0.5679, 0.8488] | 18 |
| ndcg@10 | 0.7038 | [0.5601, 0.8474] | 18 |

## Generation-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| **semantic_sim** | 0.8293 | [0.8037, 0.8549] | 18 |
| rouge_l_recall | 0.2650 | [0.2120, 0.3180] | 18 |
| content_f1 | 0.3227 | [0.2831, 0.3623] | 18 |
| bertscore_f1 | 0.7454 | [0.7339, 0.7570] | 18 |

## Faithfulness & Relevance (RAGAS)

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.7122 | [0.5686, 0.8557] | 18 |
| citation_precision | 0.4111 | [0.3136, 0.5086] | 18 |
| factual_consistency_score | 3.0000 | [3.0000, 3.0000] | 18 |
| **factual_consistency_normalized** | 0.5000 | [0.5000, 0.5000] | 18 |
| llm_answer_relevance | 0.6806 | [0.5699, 0.7912] | 18 |
| llm_context_relevance | 0.5556 | [0.4922, 0.6189] | 18 |
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

*Report generiert am 2025-12-14 14:06:53*