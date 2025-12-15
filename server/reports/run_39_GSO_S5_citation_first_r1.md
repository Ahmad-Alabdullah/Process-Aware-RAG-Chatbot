# Evaluation Report: GSO_S5_citation_first_r1

**Run ID:** 39
**Erstellt:** 2025-12-14 13:06:53
**Dataset:** demo

---

## Konfiguration

```yaml
model: qwen2.5:7b-instruct
top_k: 5
use_rerank: False
prompt_style: citation_first
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
| **semantic_sim** | 0.8227 | [0.7963, 0.8491] | 18 |
| rouge_l_recall | 0.2208 | [0.1967, 0.2449] | 18 |
| content_f1 | 0.3185 | [0.2901, 0.3468] | 18 |
| bertscore_f1 | 0.7399 | [0.7286, 0.7513] | 18 |

## Faithfulness & Relevance (RAGAS)

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.7612 | [0.6108, 0.9117] | 18 |
| citation_precision | 0.4000 | [0.2949, 0.5051] | 18 |
| factual_consistency_score | 3.0000 | [3.0000, 3.0000] | 18 |
| **factual_consistency_normalized** | 0.5000 | [0.5000, 0.5000] | 18 |
| llm_answer_relevance | 0.5000 | [0.5000, 0.5000] | 18 |
| llm_context_relevance | 0.5833 | [0.5273, 0.6394] | 18 |
| llm_faithfulness | 0.6806 | [0.5699, 0.7912] | 18 |

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

*Report generiert am 2025-12-14 14:18:43*