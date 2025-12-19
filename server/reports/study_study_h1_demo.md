# Study Report: study_h1_demo

**Baseline:** H1_HYBRID_DEMO
**Varianten:** 4
**Primäre Metriken:** recall@5, ndcg@5, mrr@5, factual_consistency_normalized, llm_answer_relevance, llm_context_relevance, llm_faithfulness, semantic_sim

---

## Übersicht: Primäre Metriken

| Variante | recall@5 | ndcg@5 | mrr@5 | factual_consistency_normalized | llm_answer_relevance | llm_context_relevance | llm_faithfulness | semantic_sim |
|----------|---:|---:|---:|---:|---:|---:|---:|---:|
| **H1_HYBRID_DEMO** (Baseline) | 0.7330 | 0.7887 | 0.9306 | 0.5139 | 0.6019 | 0.5556 | 0.6250 | 0.8465 |
| H1_VECTOR_ONLY (n=3) | 0.7612 (↑ +0.0282) | 0.7700 (↓ -0.0187) | 0.9074 (↓ -0.0231) | 0.5139 ± 0.0241 (≈0) | 0.5741 ± 0.0160 (↓ -0.0278) | 0.5833 (↑ +0.0278) | 0.6204 ± 0.0080 (↓ -0.0046) | 0.8477 ± 0.0040 (↑ +0.0012) |
| H1_VECTOR_ONLY_RERANK (n=3) | 0.7631 (↑ +0.0301) | 0.7813 (↓ -0.0074) | 0.9630 (↑ +0.0324) | 0.5093 ± 0.0160 (↓ -0.0046) | 0.6389 ± 0.0278 (↑ +0.0370) | 0.5278 (↓ -0.0278) | 0.6296 ± 0.0160 (↑ +0.0046) | 0.8467 ± 0.0040 (≈0) |
| H1_BM25_ONLY (n=3) | 0.7608 (↑ +0.0278) | 0.7832 (↓ -0.0055) | 0.8935 (↓ -0.0370) | 0.5000 (↓ -0.0139) | 0.6157 ± 0.1114 (↑ +0.0139*) | 0.5278 (↓ -0.0278) | 0.6019 ± 0.0321 (↓ -0.0231) | 0.8359 ± 0.0091 (↓ -0.0106) |
| H1_BM25_ONLY_RERANK (n=3) | 0.7631 (↑ +0.0301) | 0.7813 (↓ -0.0074) | 0.9630 (↑ +0.0324) | 0.5370 ± 0.0350 (↑ +0.0231) | 0.6343 ± 0.0401 (↑ +0.0324) | 0.5278 (↓ -0.0278) | 0.5926 ± 0.0212 (↓ -0.0324) | 0.8414 ± 0.0050 (↓ -0.0051) |

*Signifikanz: *** p<0.001, ** p<0.01, * p<0.05*

## Ranking nach recall@5

1. **H1_VECTOR_ONLY_RERANK**: 0.7631
2. **H1_BM25_ONLY_RERANK**: 0.7631
3. **H1_VECTOR_ONLY**: 0.7612
4. **H1_BM25_ONLY**: 0.7608
5. **H1_HYBRID_DEMO** (Baseline): 0.7330

## Ranking nach ndcg@5

1. **H1_HYBRID_DEMO** (Baseline): 0.7887
2. **H1_BM25_ONLY**: 0.7832
3. **H1_VECTOR_ONLY_RERANK**: 0.7813
4. **H1_BM25_ONLY_RERANK**: 0.7813
5. **H1_VECTOR_ONLY**: 0.7700

## Ranking nach mrr@5

1. **H1_VECTOR_ONLY_RERANK**: 0.9630
2. **H1_BM25_ONLY_RERANK**: 0.9630
3. **H1_HYBRID_DEMO** (Baseline): 0.9306
4. **H1_VECTOR_ONLY**: 0.9074
5. **H1_BM25_ONLY**: 0.8935

## Ranking nach factual_consistency_normalized

1. **H1_BM25_ONLY_RERANK**: 0.5370
2. **H1_HYBRID_DEMO** (Baseline): 0.5139
3. **H1_VECTOR_ONLY**: 0.5139
4. **H1_VECTOR_ONLY_RERANK**: 0.5093
5. **H1_BM25_ONLY**: 0.5000

## Ranking nach llm_answer_relevance

1. **H1_VECTOR_ONLY_RERANK**: 0.6389
2. **H1_BM25_ONLY_RERANK**: 0.6343
3. **H1_BM25_ONLY**: 0.6157
4. **H1_HYBRID_DEMO** (Baseline): 0.6019
5. **H1_VECTOR_ONLY**: 0.5741

## Ranking nach llm_context_relevance

1. **H1_VECTOR_ONLY**: 0.5833
2. **H1_HYBRID_DEMO** (Baseline): 0.5556
3. **H1_VECTOR_ONLY_RERANK**: 0.5278
4. **H1_BM25_ONLY**: 0.5278
5. **H1_BM25_ONLY_RERANK**: 0.5278

## Ranking nach llm_faithfulness

1. **H1_VECTOR_ONLY_RERANK**: 0.6296
2. **H1_HYBRID_DEMO** (Baseline): 0.6250
3. **H1_VECTOR_ONLY**: 0.6204
4. **H1_BM25_ONLY**: 0.6019
5. **H1_BM25_ONLY_RERANK**: 0.5926

## Ranking nach semantic_sim

1. **H1_VECTOR_ONLY**: 0.8477
2. **H1_VECTOR_ONLY_RERANK**: 0.8467
3. **H1_HYBRID_DEMO** (Baseline): 0.8465
4. **H1_BM25_ONLY_RERANK**: 0.8414
5. **H1_BM25_ONLY**: 0.8359


---

## Detailvergleiche

### H1_VECTOR_ONLY

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.7330 | 0.7612 | ↑ +0.0282 |  |
| ndcg@5 | 0.7887 | 0.7700 | ↓ -0.0187 |  |
| mrr@5 | 0.9306 | 0.9074 | ↓ -0.0231 |  |
| factual_consistency_normalized | 0.5139 | 0.5139 | ≈0 |  |
| llm_answer_relevance | 0.6019 | 0.5741 | ↓ -0.0278 |  |
| llm_context_relevance | 0.5556 | 0.5833 | ↑ +0.0278 |  |
| llm_faithfulness | 0.6250 | 0.6204 | ↓ -0.0046 |  |
| semantic_sim | 0.8465 | 0.8477 | ↑ +0.0012 |  |
| recall@3 | 0.6584 | 0.6542 | ↓ -0.0042 |  |
| recall@10 | 0.7330 | 0.7612 | ↑ +0.0282 |  |
| bertscore_f1 | 0.7471 | 0.7448 | ↓ -0.0024 | * |
| content_f1 | 0.3226 | 0.3202 | ↓ -0.0024 | * |
| citation_recall | 0.7330 | 0.7612 | ↑ +0.0282 |  |


### H1_VECTOR_ONLY_RERANK

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.7330 | 0.7631 | ↑ +0.0301 |  |
| ndcg@5 | 0.7887 | 0.7813 | ↓ -0.0074 |  |
| mrr@5 | 0.9306 | 0.9630 | ↑ +0.0324 |  |
| factual_consistency_normalized | 0.5139 | 0.5093 | ↓ -0.0046 |  |
| llm_answer_relevance | 0.6019 | 0.6389 | ↑ +0.0370 |  |
| llm_context_relevance | 0.5556 | 0.5278 | ↓ -0.0278 |  |
| llm_faithfulness | 0.6250 | 0.6296 | ↑ +0.0046 |  |
| semantic_sim | 0.8465 | 0.8467 | ≈0 |  |
| recall@3 | 0.6584 | 0.6565 | ↓ -0.0019 |  |
| recall@10 | 0.7330 | 0.7631 | ↑ +0.0301 |  |
| bertscore_f1 | 0.7471 | 0.7455 | ↓ -0.0016 |  |
| content_f1 | 0.3226 | 0.3105 | ↓ -0.0121 |  |
| citation_recall | 0.7330 | 0.7631 | ↑ +0.0301 |  |


### H1_BM25_ONLY

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.7330 | 0.7608 | ↑ +0.0278 |  |
| ndcg@5 | 0.7887 | 0.7832 | ↓ -0.0055 |  |
| mrr@5 | 0.9306 | 0.8935 | ↓ -0.0370 |  |
| factual_consistency_normalized | 0.5139 | 0.5000 | ↓ -0.0139 |  |
| llm_answer_relevance | 0.6019 | 0.6157 | ↑ +0.0139 | * |
| llm_context_relevance | 0.5556 | 0.5278 | ↓ -0.0278 |  |
| llm_faithfulness | 0.6250 | 0.6019 | ↓ -0.0231 |  |
| semantic_sim | 0.8465 | 0.8359 | ↓ -0.0106 |  |
| recall@3 | 0.6584 | 0.6319 | ↓ -0.0265 |  |
| recall@10 | 0.7330 | 0.7608 | ↑ +0.0278 |  |
| bertscore_f1 | 0.7471 | 0.7440 | ↓ -0.0032 |  |
| content_f1 | 0.3226 | 0.3198 | ↓ -0.0028 |  |
| citation_recall | 0.7330 | 0.7608 | ↑ +0.0278 |  |


### H1_BM25_ONLY_RERANK

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.7330 | 0.7631 | ↑ +0.0301 |  |
| ndcg@5 | 0.7887 | 0.7813 | ↓ -0.0074 |  |
| mrr@5 | 0.9306 | 0.9630 | ↑ +0.0324 |  |
| factual_consistency_normalized | 0.5139 | 0.5370 | ↑ +0.0231 |  |
| llm_answer_relevance | 0.6019 | 0.6343 | ↑ +0.0324 |  |
| llm_context_relevance | 0.5556 | 0.5278 | ↓ -0.0278 |  |
| llm_faithfulness | 0.6250 | 0.5926 | ↓ -0.0324 |  |
| semantic_sim | 0.8465 | 0.8414 | ↓ -0.0051 |  |
| recall@3 | 0.6584 | 0.6565 | ↓ -0.0019 |  |
| recall@10 | 0.7330 | 0.7631 | ↑ +0.0301 |  |
| bertscore_f1 | 0.7471 | 0.7451 | ↓ -0.0020 |  |
| content_f1 | 0.3226 | 0.3143 | ↓ -0.0084 |  |
| citation_recall | 0.7330 | 0.7631 | ↑ +0.0301 |  |


---

*Report generiert am 2025-12-18 15:48:36*