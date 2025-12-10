# Evaluation Report: OFAT_embed_qwen3_bytitle

**Run ID:** 45
**Erstellt:** 2025-12-10 14:25:30
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
| recall@3 | 0.6329 | [0.4858, 0.7800] | 18 |
| **recall@5** | 0.7218 | [0.5847, 0.8588] | 18 |
| recall@10 | 0.7218 | [0.5847, 0.8588] | 18 |
| mrr@3 | 0.9352 | [0.8470, 1.0233] | 18 |
| mrr@5 | 0.9352 | [0.8470, 1.0233] | 18 |
| mrr@10 | 0.9352 | [0.8470, 1.0233] | 18 |
| ndcg@3 | 0.7091 | [0.5743, 0.8438] | 18 |
| ndcg@5 | 0.7340 | [0.6011, 0.8668] | 18 |
| ndcg@10 | 0.7289 | [0.5920, 0.8658] | 18 |

## Generation-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| **semantic_sim** | 0.8215 | [0.7734, 0.8695] | 18 |
| rouge_l_recall | 0.2731 | [0.2113, 0.3349] | 18 |
| content_f1 | 0.2981 | [0.2555, 0.3407] | 18 |
| bertscore_f1 | 0.7324 | [0.7181, 0.7467] | 18 |

## Faithfulness-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.7218 | [0.5847, 0.8588] | 18 |
| citation_precision | 0.4333 | [0.3270, 0.5396] | 18 |
| factual_consistency_score | 3.0556 | [2.9467, 3.1644] | 18 |
| **factual_consistency_normalized** | 0.5139 | [0.4867, 0.5411] | 18 |

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

*Report generiert am 2025-12-10 15:35:52*