# Evaluation Report: H1_BM25_ONLY_r3

**Run ID:** 97
**Erstellt:** 2025-12-18 14:05:24
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
| **semantic_sim** | 0.8463 | [0.8232, 0.8694] | 18 |
| rouge_l_recall | 0.2500 | [0.2257, 0.2743] | 18 |
| content_f1 | 0.3242 | [0.2948, 0.3537] | 18 |
| bertscore_f1 | 0.7463 | [0.7366, 0.7561] | 18 |

## Faithfulness & Relevance (RAGAS)

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.7608 | [0.6466, 0.8749] | 18 |
| citation_precision | 0.4222 | [0.3390, 0.5054] | 18 |
| factual_consistency_score | 3.0000 | [3.0000, 3.0000] | 18 |
| **factual_consistency_normalized** | 0.5000 | [0.5000, 0.5000] | 18 |
| llm_faithfulness | 0.5833 | [0.5147, 0.6519] | 18 |

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

*Report generiert am 2025-12-18 15:12:48*