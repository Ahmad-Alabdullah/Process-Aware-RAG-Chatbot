# Evaluation Report: ENHANCED_BASELINE_SYNTHETIC_GEMMA3_r3

**Run ID:** 47
**Erstellt:** 2025-12-16 23:49:31
**Dataset:** synthetic_gemma3

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
| recall@3 | 0.6452 | [0.5321, 0.7583] | 31 |
| **recall@5** | 0.7581 | [0.6578, 0.8584] | 31 |
| recall@10 | 0.7581 | [0.6578, 0.8584] | 31 |
| mrr@3 | 0.7688 | [0.6424, 0.8953] | 31 |
| mrr@5 | 0.7849 | [0.6696, 0.9003] | 31 |
| mrr@10 | 0.7849 | [0.6696, 0.9003] | 31 |
| ndcg@3 | 0.6188 | [0.5160, 0.7216] | 31 |
| ndcg@5 | 0.6727 | [0.5899, 0.7554] | 31 |
| ndcg@10 | 0.6727 | [0.5899, 0.7554] | 31 |

## Generation-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| **semantic_sim** | 0.7962 | [0.7675, 0.8249] | 31 |
| rouge_l_recall | 0.4629 | [0.3919, 0.5339] | 31 |
| content_f1 | 0.2736 | [0.2239, 0.3233] | 31 |
| bertscore_f1 | 0.7495 | [0.7324, 0.7665] | 31 |

## Faithfulness & Relevance (RAGAS)

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.7581 | [0.6578, 0.8584] | 31 |
| citation_precision | 0.2194 | [0.1915, 0.2473] | 31 |
| factual_consistency_score | 3.0645 | [2.9766, 3.1524] | 31 |
| **factual_consistency_normalized** | 0.5161 | [0.4942, 0.5381] | 31 |
| llm_answer_relevance | 0.7339 | [0.6490, 0.8187] | 31 |
| llm_context_relevance | 0.5081 | [0.4599, 0.5562] | 31 |
| llm_faithfulness | 0.5968 | [0.5338, 0.6597] | 31 |

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

*Report generiert am 2025-12-17 01:03:14*