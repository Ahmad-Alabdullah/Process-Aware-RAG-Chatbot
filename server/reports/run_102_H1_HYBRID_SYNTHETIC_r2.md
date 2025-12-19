# Evaluation Report: H1_HYBRID_SYNTHETIC_r2

**Run ID:** 102
**Erstellt:** 2025-12-18 15:09:11
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
| **semantic_sim** | 0.8030 | [0.7754, 0.8307] | 31 |
| rouge_l_recall | 0.4961 | [0.4213, 0.5709] | 31 |
| content_f1 | 0.2984 | [0.2405, 0.3563] | 31 |
| bertscore_f1 | 0.7572 | [0.7416, 0.7727] | 31 |

## Faithfulness & Relevance (RAGAS)

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.7581 | [0.6578, 0.8584] | 31 |
| citation_precision | 0.2194 | [0.1915, 0.2473] | 31 |
| factual_consistency_score | 3.0323 | [2.9690, 3.0955] | 31 |
| **factual_consistency_normalized** | 0.5081 | [0.4923, 0.5239] | 31 |
| llm_answer_relevance | 0.6129 | [0.5416, 0.6842] | 31 |
| llm_context_relevance | 0.5081 | [0.4599, 0.5562] | 31 |
| llm_faithfulness | 0.5806 | [0.5279, 0.6334] | 31 |

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

*Report generiert am 2025-12-18 16:22:39*