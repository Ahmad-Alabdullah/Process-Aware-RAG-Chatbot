# Evaluation Report: H1_HYBRID_DEMO_r2

**Run ID:** 87
**Erstellt:** 2025-12-18 12:32:49
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
| recall@3 | 0.6584 | [0.5018, 0.8150] | 18 |
| **recall@5** | 0.7330 | [0.5970, 0.8690] | 18 |
| recall@10 | 0.7330 | [0.5970, 0.8690] | 18 |
| mrr@3 | 0.9167 | [0.7978, 1.0355] | 18 |
| mrr@5 | 0.9306 | [0.8351, 1.0260] | 18 |
| mrr@10 | 0.9306 | [0.8351, 1.0260] | 18 |
| ndcg@3 | 0.7706 | [0.6357, 0.9055] | 18 |
| ndcg@5 | 0.7887 | [0.6714, 0.9060] | 18 |
| ndcg@10 | 0.7833 | [0.6611, 0.9055] | 18 |

## Generation-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| **semantic_sim** | 0.8469 | [0.8271, 0.8668] | 18 |
| rouge_l_recall | 0.2747 | [0.2416, 0.3078] | 18 |
| content_f1 | 0.3274 | [0.2923, 0.3625] | 18 |
| bertscore_f1 | 0.7441 | [0.7347, 0.7535] | 18 |

## Faithfulness & Relevance (RAGAS)

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.7330 | [0.5970, 0.8690] | 18 |
| citation_precision | 0.3889 | [0.3023, 0.4755] | 18 |
| factual_consistency_score | 3.1111 | [2.8933, 3.3289] | 18 |
| **factual_consistency_normalized** | 0.5278 | [0.4733, 0.5822] | 18 |
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

*Report generiert am 2025-12-18 13:40:56*