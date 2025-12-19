# Evaluation Report: H1_BM25_ONLY_SYN_r3

**Run ID:** 123
**Erstellt:** 2025-12-18 20:22:40
**Dataset:** synthetic_gemma3

---

## Konfiguration

```yaml
model: qwen2.5:7b-instruct
top_k: 5
use_rerank: False
prompt_style: cot
retrieval_mode: bm25_only
rrf_k: 60
```

## Retrieval-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| recall@3 | 0.5000 | [0.3637, 0.6363] | 31 |
| **recall@5** | 0.5645 | [0.4301, 0.6989] | 31 |
| recall@10 | 0.5645 | [0.4301, 0.6989] | 31 |
| mrr@3 | 0.6398 | [0.4801, 0.7995] | 31 |
| mrr@5 | 0.6543 | [0.5010, 0.8076] | 31 |
| mrr@10 | 0.6543 | [0.5010, 0.8076] | 31 |
| ndcg@3 | 0.5131 | [0.3750, 0.6511] | 31 |
| ndcg@5 | 0.5426 | [0.4125, 0.6727] | 31 |
| ndcg@10 | 0.5426 | [0.4125, 0.6727] | 31 |

## Generation-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| **semantic_sim** | 0.7554 | [0.7149, 0.7959] | 31 |
| rouge_l_recall | 0.4475 | [0.3556, 0.5395] | 31 |
| content_f1 | 0.2389 | [0.1853, 0.2925] | 31 |
| bertscore_f1 | 0.7382 | [0.7174, 0.7589] | 31 |

## Faithfulness & Relevance (RAGAS)

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.5645 | [0.4301, 0.6989] | 31 |
| citation_precision | 0.1742 | [0.1346, 0.2138] | 31 |
| factual_consistency_score | 3.0645 | [2.9766, 3.1524] | 31 |
| **factual_consistency_normalized** | 0.5161 | [0.4942, 0.5381] | 31 |
| llm_answer_relevance | 0.5887 | [0.5306, 0.6469] | 31 |
| llm_context_relevance | 0.4677 | [0.4133, 0.5222] | 31 |
| llm_faithfulness | 0.5887 | [0.5352, 0.6422] | 31 |

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

*Report generiert am 2025-12-18 21:35:46*