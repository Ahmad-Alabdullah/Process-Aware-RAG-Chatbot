# Evaluation Report: H1_VECTOR_ONLY_SYN_r3

**Run ID:** 117
**Erstellt:** 2025-12-18 18:52:39
**Dataset:** synthetic_gemma3

---

## Konfiguration

```yaml
model: qwen2.5:7b-instruct
top_k: 5
use_rerank: False
prompt_style: cot
retrieval_mode: vector_only
rrf_k: 60
```

## Retrieval-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| recall@3 | 0.6290 | [0.5091, 0.7490] | 31 |
| **recall@5** | 0.7419 | [0.6525, 0.8314] | 31 |
| recall@10 | 0.7419 | [0.6525, 0.8314] | 31 |
| mrr@3 | 0.7151 | [0.5846, 0.8455] | 31 |
| mrr@5 | 0.7457 | [0.6351, 0.8563] | 31 |
| mrr@10 | 0.7457 | [0.6351, 0.8563] | 31 |
| ndcg@3 | 0.5866 | [0.4798, 0.6934] | 31 |
| ndcg@5 | 0.6391 | [0.5594, 0.7188] | 31 |
| ndcg@10 | 0.6391 | [0.5594, 0.7188] | 31 |

## Generation-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| **semantic_sim** | 0.7946 | [0.7664, 0.8228] | 31 |
| rouge_l_recall | 0.4936 | [0.4076, 0.5795] | 31 |
| content_f1 | 0.2729 | [0.2194, 0.3264] | 31 |
| bertscore_f1 | 0.7500 | [0.7286, 0.7714] | 31 |

## Faithfulness & Relevance (RAGAS)

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.7419 | [0.6525, 0.8314] | 31 |
| citation_precision | 0.2065 | [0.1938, 0.2191] | 31 |
| factual_consistency_score | 3.0323 | [2.9690, 3.0955] | 31 |
| **factual_consistency_normalized** | 0.5081 | [0.4923, 0.5239] | 31 |
| llm_answer_relevance | 0.5968 | [0.5298, 0.6637] | 31 |
| llm_context_relevance | 0.5081 | [0.4657, 0.5505] | 31 |
| llm_faithfulness | 0.5323 | [0.4946, 0.5699] | 31 |

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

*Report generiert am 2025-12-18 20:04:48*