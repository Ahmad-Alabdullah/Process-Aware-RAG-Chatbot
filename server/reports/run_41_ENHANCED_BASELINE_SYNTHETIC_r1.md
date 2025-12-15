# Evaluation Report: ENHANCED_BASELINE_SYNTHETIC_r1

**Run ID:** 41
**Erstellt:** 2025-12-15 17:23:52
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
| **semantic_sim** | 0.8501 | [0.8336, 0.8666] | 48 |
| rouge_l_recall | 0.4919 | [0.4436, 0.5402] | 48 |
| content_f1 | 0.4067 | [0.3601, 0.4532] | 48 |
| bertscore_f1 | 0.7732 | [0.7594, 0.7870] | 48 |

## Faithfulness & Relevance (RAGAS)

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.9062 | [0.8505, 0.9620] | 48 |
| citation_precision | 0.2833 | [0.2551, 0.3115] | 48 |
| factual_consistency_score | 3.1042 | [2.9991, 3.2092] | 48 |
| **factual_consistency_normalized** | 0.5260 | [0.4998, 0.5523] | 48 |
| llm_answer_relevance | 0.7135 | [0.6483, 0.7788] | 48 |
| llm_context_relevance | 0.4740 | [0.4406, 0.5074] | 48 |
| llm_faithfulness | 0.6198 | [0.5652, 0.6744] | 48 |

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

*Report generiert am 2025-12-15 18:46:07*