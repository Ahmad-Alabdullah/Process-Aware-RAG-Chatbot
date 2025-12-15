# Evaluation Report: ENHANCED_BASELINE_r3

**Run ID:** 36
**Erstellt:** 2025-12-14 11:51:51
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
| **semantic_sim** | 0.8576 | [0.8426, 0.8726] | 18 |
| rouge_l_recall | 0.2715 | [0.2219, 0.3212] | 18 |
| content_f1 | 0.3267 | [0.2839, 0.3696] | 18 |
| bertscore_f1 | 0.7535 | [0.7442, 0.7628] | 18 |

## Faithfulness & Relevance (RAGAS)

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.7612 | [0.6108, 0.9117] | 18 |
| citation_precision | 0.4000 | [0.2949, 0.5051] | 18 |
| factual_consistency_score | 3.1111 | [2.8933, 3.3289] | 18 |
| **factual_consistency_normalized** | 0.5278 | [0.4733, 0.5822] | 18 |
| llm_answer_relevance | 0.6667 | [0.5546, 0.7787] | 18 |
| llm_context_relevance | 0.5833 | [0.5273, 0.6394] | 18 |
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

*Report generiert am 2025-12-14 13:00:02*