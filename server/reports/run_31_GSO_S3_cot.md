# Evaluation Report: GSO_S3_cot

**Run ID:** 31
**Erstellt:** 2025-12-13 15:39:45
**Dataset:** demo

---

## Konfiguration

```yaml
model: qwen3:8b
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
| **semantic_sim** | 0.8389 | [0.8165, 0.8613] | 17 |
| rouge_l_recall | 0.2691 | [0.2100, 0.3281] | 17 |
| content_f1 | 0.3242 | [0.2860, 0.3625] | 17 |
| bertscore_f1 | 0.7356 | [0.7235, 0.7478] | 17 |

## Faithfulness & Relevance (RAGAS)

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.7707 | [0.6124, 0.9291] | 17 |
| citation_precision | 0.3882 | [0.2795, 0.4970] | 17 |
| factual_consistency_score | 3.2941 | [2.9680, 3.6202] | 17 |
| **factual_consistency_normalized** | 0.5735 | [0.4920, 0.6551] | 17 |
| llm_answer_relevance | 0.5882 | [0.4948, 0.6816] | 17 |
| llm_context_relevance | 0.5882 | [0.5297, 0.6468] | 17 |
| llm_faithfulness | 0.5882 | [0.5048, 0.6716] | 17 |

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

*Report generiert am 2025-12-13 16:53:42*