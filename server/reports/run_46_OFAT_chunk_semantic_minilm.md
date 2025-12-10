# Evaluation Report: OFAT_chunk_semantic_minilm

**Run ID:** 46
**Erstellt:** 2025-12-10 14:35:52
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
| recall@3 | 0.3549 | [0.1602, 0.5497] | 18 |
| **recall@5** | 0.4235 | [0.2426, 0.6043] | 18 |
| recall@10 | 0.4235 | [0.2426, 0.6043] | 18 |
| mrr@3 | 0.4352 | [0.2658, 0.6046] | 18 |
| mrr@5 | 0.4602 | [0.3023, 0.6180] | 18 |
| mrr@10 | 0.4602 | [0.3023, 0.6180] | 18 |
| ndcg@3 | 0.3167 | [0.1934, 0.4401] | 18 |
| ndcg@5 | 0.3496 | [0.2393, 0.4598] | 18 |
| ndcg@10 | 0.3244 | [0.2175, 0.4312] | 18 |

## Generation-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| **semantic_sim** | 0.8236 | [0.7964, 0.8508] | 17 |
| rouge_l_recall | 0.2361 | [0.1954, 0.2769] | 17 |
| content_f1 | 0.2844 | [0.2435, 0.3253] | 17 |
| bertscore_f1 | 0.7266 | [0.7169, 0.7363] | 17 |

## Faithfulness-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.4248 | [0.2330, 0.6167] | 17 |
| citation_precision | 0.2588 | [0.1714, 0.3462] | 17 |
| factual_consistency_score | 3.0588 | [2.9435, 3.1741] | 17 |
| **factual_consistency_normalized** | 0.5147 | [0.4859, 0.5435] | 17 |

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

*Report generiert am 2025-12-10 15:45:10*