# Evaluation Report: H1_HYBRID_DEMO_r3

**Run ID:** 88
**Erstellt:** 2025-12-18 12:40:56
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
| **semantic_sim** | 0.8473 | [0.8275, 0.8670] | 18 |
| rouge_l_recall | 0.2556 | [0.2094, 0.3018] | 18 |
| content_f1 | 0.3113 | [0.2732, 0.3494] | 18 |
| bertscore_f1 | 0.7482 | [0.7413, 0.7550] | 18 |

## Faithfulness & Relevance (RAGAS)

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.7330 | [0.5970, 0.8690] | 18 |
| citation_precision | 0.3889 | [0.3023, 0.4755] | 18 |
| factual_consistency_score | 3.0556 | [2.9467, 3.1644] | 18 |
| **factual_consistency_normalized** | 0.5139 | [0.4867, 0.5411] | 18 |
| llm_faithfulness | 0.6528 | [0.5630, 0.7426] | 18 |

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

*Report generiert am 2025-12-18 13:49:04*