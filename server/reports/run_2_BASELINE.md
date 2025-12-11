# Evaluation Report: BASELINE

**Run ID:** 2
**Erstellt:** 2025-12-11 12:30:04
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
| recall@3 | 0.5421 | [0.3854, 0.6989] | 18 |
| **recall@5** | 0.6597 | [0.5195, 0.7999] | 18 |
| recall@10 | 0.6597 | [0.5195, 0.7999] | 18 |
| mrr@3 | 0.8056 | [0.6510, 0.9601] | 18 |
| mrr@5 | 0.8194 | [0.6795, 0.9593] | 18 |
| mrr@10 | 0.8194 | [0.6795, 0.9593] | 18 |
| ndcg@3 | 0.6129 | [0.4457, 0.7800] | 18 |
| ndcg@5 | 0.6664 | [0.5256, 0.8072] | 18 |
| ndcg@10 | 0.6624 | [0.5190, 0.8057] | 18 |

## Generation-Metriken

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| **semantic_sim** | 0.8302 | [0.8084, 0.8519] | 16 |
| rouge_l_recall | 0.2653 | [0.2274, 0.3031] | 16 |
| content_f1 | 0.3060 | [0.2743, 0.3377] | 16 |
| bertscore_f1 | 0.7364 | [0.7278, 0.7449] | 16 |

## Faithfulness & Relevance (RAGAS)

| Metrik | Mean | 95% CI | N |
|--------|-----:|--------|--:|
| citation_recall | 0.6714 | [0.5197, 0.8230] | 16 |
| citation_precision | 0.3750 | [0.2812, 0.4688] | 16 |
| factual_consistency_score | 3.0625 | [2.9400, 3.1850] | 16 |
| **factual_consistency_normalized** | 0.5156 | [0.4850, 0.5463] | 16 |
| llm_answer_relevance | 0.6250 | [0.5154, 0.7346] | 16 |
| llm_context_relevance | 0.5625 | [0.5077, 0.6173] | 16 |
| llm_faithfulness | 0.6250 | [0.5250, 0.7250] | 16 |

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

*Report generiert am 2025-12-11 14:44:52*