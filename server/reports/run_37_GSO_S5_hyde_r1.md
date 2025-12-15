# Evaluation Report: GSO_S5_hyde_r1

**Run ID:** 37
**Erstellt:** 2025-12-14 12:37:29
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
| recall@3 | 0.5983 | [0.4349, 0.7616] | 18 |
| **recall@5** | 0.7682 | [0.6337, 0.9026] | 18 |
| recall@10 | 0.7682 | [0.6337, 0.9026] | 18 |
| mrr@3 | 0.7963 | [0.6302, 0.9624] | 18 |
| mrr@5 | 0.8213 | [0.6808, 0.9618] | 18 |
| mrr@10 | 0.8213 | [0.6808, 0.9618] | 18 |
| ndcg@3 | 0.6703 | [0.5055, 0.8351] | 18 |
| ndcg@5 | 0.7378 | [0.6079, 0.8676] | 18 |
| ndcg@10 | 0.7277 | [0.5958, 0.8597] | 18 |

## Generation-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| **semantic_sim** | 0.8415 | [0.8240, 0.8591] | 18 |
| rouge_l_recall | 0.2619 | [0.2123, 0.3116] | 18 |
| content_f1 | 0.3060 | [0.2714, 0.3405] | 18 |
| bertscore_f1 | 0.7402 | [0.7313, 0.7491] | 18 |

## Faithfulness & Relevance (RAGAS)

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.7682 | [0.6337, 0.9026] | 18 |
| citation_precision | 0.4222 | [0.3277, 0.5167] | 18 |
| factual_consistency_score | 3.2222 | [2.9689, 3.4755] | 18 |
| **factual_consistency_normalized** | 0.5556 | [0.4922, 0.6189] | 18 |
| llm_answer_relevance | 0.8056 | [0.6967, 0.9144] | 18 |
| llm_context_relevance | 0.5278 | [0.4733, 0.5822] | 18 |
| llm_faithfulness | 0.6111 | [0.5297, 0.6925] | 18 |

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

*Report generiert am 2025-12-14 13:52:19*