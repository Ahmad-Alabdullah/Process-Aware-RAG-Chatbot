# Evaluation Report: H1_BM25_ONLY_SYN_RERANK_r2

**Run ID:** 125
**Erstellt:** 2025-12-18 20:49:01
**Dataset:** synthetic_gemma3

---

## Konfiguration

```yaml
model: qwen2.5:7b-instruct
top_k: 5
use_rerank: True
prompt_style: cot
retrieval_mode: bm25_only
rrf_k: 60
```

## Retrieval-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| recall@3 | 0.7097 | [0.6104, 0.8090] | 31 |
| **recall@5** | 0.7742 | [0.6742, 0.8742] | 31 |
| recall@10 | 0.7742 | [0.6742, 0.8742] | 31 |
| mrr@3 | 0.8226 | [0.7188, 0.9264] | 31 |
| mrr@5 | 0.8226 | [0.7188, 0.9264] | 31 |
| mrr@10 | 0.8226 | [0.7188, 0.9264] | 31 |
| ndcg@3 | 0.6839 | [0.5893, 0.7785] | 31 |
| ndcg@5 | 0.7153 | [0.6276, 0.8031] | 31 |
| ndcg@10 | 0.7153 | [0.6276, 0.8031] | 31 |

## Generation-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| **semantic_sim** | 0.7865 | [0.7618, 0.8112] | 31 |
| rouge_l_recall | 0.4316 | [0.3611, 0.5020] | 31 |
| content_f1 | 0.2343 | [0.1902, 0.2783] | 31 |
| bertscore_f1 | 0.7367 | [0.7223, 0.7510] | 31 |

## Faithfulness & Relevance (RAGAS)

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.7742 | [0.6742, 0.8742] | 31 |
| citation_precision | 0.2258 | [0.1957, 0.2559] | 31 |
| factual_consistency_score | 3.0000 | [3.0000, 3.0000] | 31 |
| **factual_consistency_normalized** | 0.5000 | [0.5000, 0.5000] | 31 |
| llm_answer_relevance | 0.6290 | [0.5576, 0.7004] | 31 |
| llm_context_relevance | 0.5403 | [0.4943, 0.5863] | 31 |
| llm_faithfulness | 0.5645 | [0.5090, 0.6200] | 31 |

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

*Report generiert am 2025-12-18 22:03:24*