# Evaluation Report: Q4_0_quantization

**Run ID:** 134
**Erstellt:** 2025-12-26 16:00:06
**Dataset:** demo

---

## Konfiguration

```yaml
model: qwen2.5:7b-instruct-q4_0
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
| **semantic_sim** | 0.8594 | [0.8427, 0.8761] | 18 |
| rouge_l_recall | 0.2697 | [0.2286, 0.3109] | 18 |
| content_f1 | 0.3128 | [0.2771, 0.3484] | 18 |
| bertscore_f1 | 0.7469 | [0.7374, 0.7563] | 18 |

## Faithfulness & Relevance (RAGAS)

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.7330 | [0.5970, 0.8690] | 18 |
| citation_precision | 0.3889 | [0.3023, 0.4755] | 18 |
| factual_consistency_score | 3.0000 | [3.0000, 3.0000] | 18 |
| **factual_consistency_normalized** | 0.5000 | [0.5000, 0.5000] | 18 |
| llm_answer_relevance | 0.5694 | [0.4922, 0.6467] | 18 |
| llm_context_relevance | 0.5556 | [0.5061, 0.6050] | 18 |
| llm_faithfulness | 0.5556 | [0.5061, 0.6050] | 18 |

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

*Report generiert am 2025-12-26 17:09:49*