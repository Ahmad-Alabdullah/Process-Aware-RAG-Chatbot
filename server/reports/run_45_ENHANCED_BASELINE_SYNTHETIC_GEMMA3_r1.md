# Evaluation Report: ENHANCED_BASELINE_SYNTHETIC_GEMMA3_r1

**Run ID:** 45
**Erstellt:** 2025-12-16 23:21:10
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
| **semantic_sim** | 0.7942 | [0.7630, 0.8254] | 31 |
| rouge_l_recall | 0.4979 | [0.4131, 0.5827] | 31 |
| content_f1 | 0.2716 | [0.2205, 0.3227] | 31 |
| bertscore_f1 | 0.7512 | [0.7342, 0.7681] | 31 |

## Faithfulness & Relevance (RAGAS)

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.7581 | [0.6578, 0.8584] | 31 |
| citation_precision | 0.2194 | [0.1915, 0.2473] | 31 |
| factual_consistency_score | 3.0968 | [2.9910, 3.2026] | 31 |
| **factual_consistency_normalized** | 0.5242 | [0.4977, 0.5506] | 31 |
| llm_answer_relevance | 0.6290 | [0.5541, 0.7040] | 31 |
| llm_context_relevance | 0.5081 | [0.4599, 0.5562] | 31 |
| llm_faithfulness | 0.5806 | [0.5232, 0.6381] | 31 |

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

*Report generiert am 2025-12-17 00:35:17*