# Evaluation Report: GSO_S2_rerank_on_10

**Run ID:** 26
**Erstellt:** 2025-12-13 13:57:34
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
| recall@3 | 0.6575 | [0.5153, 0.7998] | 18 |
| **recall@5** | 0.7492 | [0.6238, 0.8747] | 18 |
| recall@10 | 0.7492 | [0.6238, 0.8747] | 18 |
| mrr@3 | 0.9722 | [0.9178, 1.0267] | 18 |
| mrr@5 | 0.9722 | [0.9178, 1.0267] | 18 |
| mrr@10 | 0.9722 | [0.9178, 1.0267] | 18 |
| ndcg@3 | 0.7609 | [0.6468, 0.8750] | 18 |
| ndcg@5 | 0.7763 | [0.6689, 0.8837] | 18 |
| ndcg@10 | 0.7669 | [0.6556, 0.8782] | 18 |

## Generation-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| **semantic_sim** | 0.8318 | [0.8140, 0.8497] | 18 |
| rouge_l_recall | 0.2873 | [0.2343, 0.3404] | 18 |
| content_f1 | 0.3216 | [0.2850, 0.3582] | 18 |
| bertscore_f1 | 0.7334 | [0.7246, 0.7422] | 18 |

## Faithfulness & Relevance (RAGAS)

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.7492 | [0.6238, 0.8747] | 18 |
| citation_precision | 0.4111 | [0.3245, 0.4977] | 18 |
| factual_consistency_score | 3.1667 | [2.9290, 3.4044] | 18 |
| **factual_consistency_normalized** | 0.5417 | [0.4822, 0.6011] | 18 |
| llm_answer_relevance | 0.5833 | [0.4948, 0.6719] | 18 |
| llm_context_relevance | 0.5417 | [0.4822, 0.6011] | 18 |
| llm_faithfulness | 0.6389 | [0.5401, 0.7377] | 18 |

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

*Report generiert am 2025-12-13 15:11:27*