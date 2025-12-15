# Evaluation Report: ENHANCED_BASELINE_SYNTHETIC_r3

**Run ID:** 44
**Erstellt:** 2025-12-15 18:06:14
**Dataset:** synthetic

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
| recall@3 | 0.8438 | [0.7657, 0.9218] | 48 |
| **recall@5** | 0.9062 | [0.8505, 0.9620] | 48 |
| recall@10 | 0.9062 | [0.8505, 0.9620] | 48 |
| mrr@3 | 0.8681 | [0.7903, 0.9458] | 48 |
| mrr@5 | 0.8774 | [0.8075, 0.9473] | 48 |
| mrr@10 | 0.8774 | [0.8075, 0.9473] | 48 |
| ndcg@3 | 0.8117 | [0.7347, 0.8887] | 48 |
| ndcg@5 | 0.8386 | [0.7769, 0.9003] | 48 |
| ndcg@10 | 0.8386 | [0.7769, 0.9003] | 48 |

## Generation-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| **semantic_sim** | 0.8507 | [0.8357, 0.8658] | 48 |
| rouge_l_recall | 0.4876 | [0.4378, 0.5373] | 48 |
| content_f1 | 0.3848 | [0.3431, 0.4266] | 48 |
| bertscore_f1 | 0.7715 | [0.7592, 0.7839] | 48 |

## Faithfulness & Relevance (RAGAS)

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.9062 | [0.8505, 0.9620] | 48 |
| citation_precision | 0.2833 | [0.2551, 0.3115] | 48 |
| factual_consistency_score | 3.0833 | [2.9691, 3.1976] | 48 |
| **factual_consistency_normalized** | 0.5208 | [0.4923, 0.5494] | 48 |
| llm_answer_relevance | 0.7031 | [0.6384, 0.7678] | 48 |
| llm_context_relevance | 0.4740 | [0.4406, 0.5074] | 48 |
| llm_faithfulness | 0.6302 | [0.5666, 0.6938] | 48 |

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

*Report generiert am 2025-12-15 19:26:24*