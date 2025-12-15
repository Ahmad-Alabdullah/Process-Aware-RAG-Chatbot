# Evaluation Report: SENTENCE_SEMANTIC

**Run ID:** 22
**Erstellt:** 2025-12-13 12:53:58
**Dataset:** demo

---

## Konfiguration

```yaml
model: qwen3:8b
top_k: 5
use_rerank: False
prompt_style: baseline
retrieval_mode: hybrid
rrf_k: 60
```

## Retrieval-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| recall@3 | 0.2778 | [0.0649, 0.4907] | 18 |
| **recall@5** | 0.2778 | [0.0649, 0.4907] | 18 |
| recall@10 | 0.2778 | [0.0649, 0.4907] | 18 |
| mrr@3 | 0.2778 | [0.0649, 0.4907] | 18 |
| mrr@5 | 0.2778 | [0.0649, 0.4907] | 18 |
| mrr@10 | 0.2778 | [0.0649, 0.4907] | 18 |
| ndcg@3 | 0.2778 | [0.0649, 0.4907] | 18 |
| ndcg@5 | 0.2778 | [0.0649, 0.4907] | 18 |
| ndcg@10 | 0.2778 | [0.0649, 0.4907] | 18 |

## Generation-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| **semantic_sim** | 0.8386 | [0.8143, 0.8630] | 18 |
| rouge_l_recall | 0.2818 | [0.2306, 0.3330] | 18 |
| content_f1 | 0.3234 | [0.2870, 0.3598] | 18 |
| bertscore_f1 | 0.7333 | [0.7227, 0.7439] | 18 |

## Faithfulness & Relevance (RAGAS)

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.2778 | [0.0649, 0.4907] | 18 |
| citation_precision | 0.0556 | [0.0130, 0.0981] | 18 |
| factual_consistency_score | 3.0556 | [2.9467, 3.1644] | 18 |
| **factual_consistency_normalized** | 0.5139 | [0.4867, 0.5411] | 18 |
| llm_answer_relevance | 0.6111 | [0.5206, 0.7016] | 18 |
| llm_context_relevance | 0.5417 | [0.4974, 0.5860] | 18 |
| llm_faithfulness | 0.5556 | [0.4922, 0.6189] | 18 |

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

*Report generiert am 2025-12-13 14:07:33*