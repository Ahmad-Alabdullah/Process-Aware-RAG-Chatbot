# Evaluation Report: H1_VECTOR_ONLY_SYN_RERANK_r3

**Run ID:** 120
**Erstellt:** 2025-12-18 19:37:33
**Dataset:** synthetic_gemma3

---

## Konfiguration

```yaml
model: qwen2.5:7b-instruct
top_k: 5
use_rerank: True
prompt_style: cot
retrieval_mode: vector_only
rrf_k: 60
```

## Retrieval-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| recall@3 | 0.7258 | [0.6368, 0.8148] | 31 |
| **recall@5** | 0.7903 | [0.7020, 0.8786] | 31 |
| recall@10 | 0.7903 | [0.7020, 0.8786] | 31 |
| mrr@3 | 0.8548 | [0.7655, 0.9441] | 31 |
| mrr@5 | 0.8548 | [0.7655, 0.9441] | 31 |
| mrr@10 | 0.8548 | [0.7655, 0.9441] | 31 |
| ndcg@3 | 0.7062 | [0.6216, 0.7908] | 31 |
| ndcg@5 | 0.7386 | [0.6627, 0.8144] | 31 |
| ndcg@10 | 0.7386 | [0.6627, 0.8144] | 31 |

## Generation-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| **semantic_sim** | 0.7793 | [0.7504, 0.8083] | 31 |
| rouge_l_recall | 0.4928 | [0.4212, 0.5643] | 31 |
| content_f1 | 0.2784 | [0.2345, 0.3223] | 31 |
| bertscore_f1 | 0.7488 | [0.7349, 0.7627] | 31 |

## Faithfulness & Relevance (RAGAS)

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.7903 | [0.7020, 0.8786] | 31 |
| citation_precision | 0.2258 | [0.2018, 0.2498] | 31 |
| factual_consistency_score | 3.1613 | [2.9773, 3.3453] | 31 |
| **factual_consistency_normalized** | 0.5403 | [0.4943, 0.5863] | 31 |
| llm_answer_relevance | 0.5968 | [0.5338, 0.6597] | 31 |
| llm_context_relevance | 0.5403 | [0.4943, 0.5863] | 31 |
| llm_faithfulness | 0.5806 | [0.5232, 0.6381] | 31 |

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

*Report generiert am 2025-12-18 20:54:30*