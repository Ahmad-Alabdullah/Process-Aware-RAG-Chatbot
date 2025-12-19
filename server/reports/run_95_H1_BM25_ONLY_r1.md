# Evaluation Report: H1_BM25_ONLY_r1

**Run ID:** 95
**Erstellt:** 2025-12-18 13:48:55
**Dataset:** demo

---

## Konfiguration

```yaml
model: qwen2.5:7b-instruct
top_k: 5
use_rerank: False
prompt_style: cot
retrieval_mode: bm25_only
rrf_k: 60
```

## Retrieval-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| recall@3 | 0.6319 | [0.4699, 0.7939] | 18 |
| **recall@5** | 0.7608 | [0.6466, 0.8749] | 18 |
| recall@10 | 0.7608 | [0.6466, 0.8749] | 18 |
| mrr@3 | 0.8796 | [0.7455, 1.0138] | 18 |
| mrr@5 | 0.8935 | [0.7785, 1.0085] | 18 |
| mrr@10 | 0.8935 | [0.7785, 1.0085] | 18 |
| ndcg@3 | 0.7187 | [0.5721, 0.8654] | 18 |
| ndcg@5 | 0.7832 | [0.6752, 0.8911] | 18 |
| ndcg@10 | 0.7744 | [0.6633, 0.8854] | 18 |

## Generation-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| **semantic_sim** | 0.8319 | [0.8065, 0.8572] | 18 |
| rouge_l_recall | 0.2692 | [0.2228, 0.3156] | 18 |
| content_f1 | 0.3247 | [0.2870, 0.3623] | 18 |
| bertscore_f1 | 0.7441 | [0.7350, 0.7532] | 18 |

## Faithfulness & Relevance (RAGAS)

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.7608 | [0.6466, 0.8749] | 18 |
| citation_precision | 0.4222 | [0.3390, 0.5054] | 18 |
| factual_consistency_score | 3.0000 | [3.0000, 3.0000] | 18 |
| **factual_consistency_normalized** | 0.5000 | [0.5000, 0.5000] | 18 |
| llm_faithfulness | 0.6389 | [0.5401, 0.7377] | 18 |

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

*Report generiert am 2025-12-18 14:57:16*