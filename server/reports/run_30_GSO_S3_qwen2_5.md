# Evaluation Report: GSO_S3_qwen2_5

**Run ID:** 30
**Erstellt:** 2025-12-13 15:30:00
**Dataset:** demo

---

## Konfiguration

```yaml
model: qwen2.5:7b-instruct
top_k: 5
use_rerank: False
prompt_style: baseline
retrieval_mode: hybrid
rrf_k: 60
```

## Retrieval-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| recall@3 | 0.6542 | [0.4998, 0.8087] | 18 |
| **recall@5** | 0.7612 | [0.6108, 0.9117] | 18 |
| recall@10 | 0.7612 | [0.6108, 0.9117] | 18 |
| mrr@3 | 0.9074 | [0.7801, 1.0347] | 18 |
| mrr@5 | 0.9074 | [0.7801, 1.0347] | 18 |
| mrr@10 | 0.9074 | [0.7801, 1.0347] | 18 |
| ndcg@3 | 0.7324 | [0.5838, 0.8811] | 18 |
| ndcg@5 | 0.7700 | [0.6280, 0.9121] | 18 |
| ndcg@10 | 0.7682 | [0.6249, 0.9116] | 18 |

## Generation-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| **semantic_sim** | 0.8468 | [0.8277, 0.8659] | 18 |
| rouge_l_recall | 0.2497 | [0.1941, 0.3053] | 18 |
| content_f1 | 0.3075 | [0.2636, 0.3515] | 18 |
| bertscore_f1 | 0.7525 | [0.7398, 0.7652] | 18 |

## Faithfulness & Relevance (RAGAS)

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.7612 | [0.6108, 0.9117] | 18 |
| citation_precision | 0.4000 | [0.2949, 0.5051] | 18 |
| factual_consistency_score | 3.1667 | [2.9895, 3.3438] | 18 |
| **factual_consistency_normalized** | 0.5417 | [0.4974, 0.5860] | 18 |
| llm_answer_relevance | 0.6111 | [0.5297, 0.6925] | 18 |
| llm_context_relevance | 0.5833 | [0.5273, 0.6394] | 18 |
| llm_faithfulness | 0.6250 | [0.5260, 0.7240] | 18 |

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

*Report generiert am 2025-12-13 16:38:44*