# Study Report: study_h1_synthetic

**Baseline:** H1_HYBRID_SYNTHETIC
**Varianten:** 4
**Primäre Metriken:** recall@5, ndcg@5, mrr@5, factual_consistency_normalized, llm_answer_relevance, llm_context_relevance, llm_faithfulness, semantic_sim

---

## Übersicht: Primäre Metriken

| Variante | recall@5 | ndcg@5 | mrr@5 | factual_consistency_normalized | llm_answer_relevance | llm_context_relevance | llm_faithfulness | semantic_sim |
|----------|---:|---:|---:|---:|---:|---:|---:|---:|
| **H1_HYBRID_SYNTHETIC** (Baseline) | 0.7581 | 0.6727 | 0.7849 | 0.5081 | 0.5941 | 0.5081 | 0.5860 | 0.7905 |
| H1_VECTOR_ONLY_SYN (n=3) | 0.7419 (↓ -0.0161) | 0.6391 (↓ -0.0336) | 0.7457 (↓ -0.0392) | 0.5161 ± 0.0213 (↑ +0.0081) | 0.6425 ± 0.0486 (↑ +0.0484**) | 0.5081 (≈0) | 0.5672 ± 0.0414 (↓ -0.0188) | 0.7922 ± 0.0063 (↑ +0.0017) |
| H1_VECTOR_ONLY_SYN_RERANK (n=3) | 0.7903 (↑ +0.0323) | 0.7386 (↑ +0.0659) | 0.8548 (↑ +0.0699) | 0.5242 ± 0.0213 (↑ +0.0161) | 0.6048 ± 0.0370 (↑ +0.0108) | 0.5403 (↑ +0.0323) | 0.5699 ± 0.0259 (↓ -0.0161) | 0.7864 ± 0.0062 (↓ -0.0041) |
| H1_BM25_ONLY_SYN (n=3) | 0.5645 (↓ -0.1935**) | 0.5426 (↓ -0.1301**) | 0.6543 (↓ -0.1306***) | 0.5134 ± 0.0123 (↑ +0.0054) | 0.5887 ± 0.0323 (↓ -0.0054) | 0.4677 (↓ -0.0403) | 0.6129 ± 0.0352 (↑ +0.0269) | 0.7523 ± 0.0046 (↓ -0.0382*) |
| H1_BM25_ONLY_SYN_RERANK (n=3) | 0.7742 (↑ +0.0161) | 0.7153 (↑ +0.0427) | 0.8226 (↑ +0.0376) | 0.5027 ± 0.0047 (↓ -0.0054) | 0.6425 ± 0.0233 (↑ +0.0484) | 0.5403 (↑ +0.0323) | 0.5672 ± 0.0203 (↓ -0.0188) | 0.7859 ± 0.0005 (↓ -0.0047) |

*Signifikanz: *** p<0.001, ** p<0.01, * p<0.05*

## Ranking nach recall@5

1. **H1_VECTOR_ONLY_SYN_RERANK**: 0.7903
2. **H1_BM25_ONLY_SYN_RERANK**: 0.7742
3. **H1_HYBRID_SYNTHETIC** (Baseline): 0.7581
4. **H1_VECTOR_ONLY_SYN**: 0.7419
5. **H1_BM25_ONLY_SYN**: 0.5645

## Ranking nach ndcg@5

1. **H1_VECTOR_ONLY_SYN_RERANK**: 0.7386
2. **H1_BM25_ONLY_SYN_RERANK**: 0.7153
3. **H1_HYBRID_SYNTHETIC** (Baseline): 0.6727
4. **H1_VECTOR_ONLY_SYN**: 0.6391
5. **H1_BM25_ONLY_SYN**: 0.5426

## Ranking nach mrr@5

1. **H1_VECTOR_ONLY_SYN_RERANK**: 0.8548
2. **H1_BM25_ONLY_SYN_RERANK**: 0.8226
3. **H1_HYBRID_SYNTHETIC** (Baseline): 0.7849
4. **H1_VECTOR_ONLY_SYN**: 0.7457
5. **H1_BM25_ONLY_SYN**: 0.6543

## Ranking nach factual_consistency_normalized

1. **H1_VECTOR_ONLY_SYN_RERANK**: 0.5242
2. **H1_VECTOR_ONLY_SYN**: 0.5161
3. **H1_BM25_ONLY_SYN**: 0.5134
4. **H1_HYBRID_SYNTHETIC** (Baseline): 0.5081
5. **H1_BM25_ONLY_SYN_RERANK**: 0.5027

## Ranking nach llm_answer_relevance

1. **H1_VECTOR_ONLY_SYN**: 0.6425
2. **H1_BM25_ONLY_SYN_RERANK**: 0.6425
3. **H1_VECTOR_ONLY_SYN_RERANK**: 0.6048
4. **H1_HYBRID_SYNTHETIC** (Baseline): 0.5941
5. **H1_BM25_ONLY_SYN**: 0.5887

## Ranking nach llm_context_relevance

1. **H1_VECTOR_ONLY_SYN_RERANK**: 0.5403
2. **H1_BM25_ONLY_SYN_RERANK**: 0.5403
3. **H1_HYBRID_SYNTHETIC** (Baseline): 0.5081
4. **H1_VECTOR_ONLY_SYN**: 0.5081
5. **H1_BM25_ONLY_SYN**: 0.4677

## Ranking nach llm_faithfulness

1. **H1_BM25_ONLY_SYN**: 0.6129
2. **H1_HYBRID_SYNTHETIC** (Baseline): 0.5860
3. **H1_VECTOR_ONLY_SYN_RERANK**: 0.5699
4. **H1_BM25_ONLY_SYN_RERANK**: 0.5672
5. **H1_VECTOR_ONLY_SYN**: 0.5672

## Ranking nach semantic_sim

1. **H1_VECTOR_ONLY_SYN**: 0.7922
2. **H1_HYBRID_SYNTHETIC** (Baseline): 0.7905
3. **H1_VECTOR_ONLY_SYN_RERANK**: 0.7864
4. **H1_BM25_ONLY_SYN_RERANK**: 0.7859
5. **H1_BM25_ONLY_SYN**: 0.7523


---

## Detailvergleiche

### H1_VECTOR_ONLY_SYN

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.7581 | 0.7419 | ↓ -0.0161 |  |
| ndcg@5 | 0.6727 | 0.6391 | ↓ -0.0336 |  |
| mrr@5 | 0.7849 | 0.7457 | ↓ -0.0392 |  |
| factual_consistency_normalized | 0.5081 | 0.5161 | ↑ +0.0081 |  |
| llm_answer_relevance | 0.5941 | 0.6425 | ↑ +0.0484 | ** |
| llm_context_relevance | 0.5081 | 0.5081 | ≈0 |  |
| llm_faithfulness | 0.5860 | 0.5672 | ↓ -0.0188 |  |
| semantic_sim | 0.7905 | 0.7922 | ↑ +0.0017 |  |
| recall@3 | 0.6452 | 0.6290 | ↓ -0.0161 |  |
| recall@10 | 0.7581 | 0.7419 | ↓ -0.0161 |  |
| bertscore_f1 | 0.7529 | 0.7466 | ↓ -0.0063 |  |
| content_f1 | 0.2822 | 0.2648 | ↓ -0.0174 |  |
| citation_recall | 0.7581 | 0.7419 | ↓ -0.0161 |  |


### H1_VECTOR_ONLY_SYN_RERANK

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.7581 | 0.7903 | ↑ +0.0323 |  |
| ndcg@5 | 0.6727 | 0.7386 | ↑ +0.0659 |  |
| mrr@5 | 0.7849 | 0.8548 | ↑ +0.0699 |  |
| factual_consistency_normalized | 0.5081 | 0.5242 | ↑ +0.0161 |  |
| llm_answer_relevance | 0.5941 | 0.6048 | ↑ +0.0108 |  |
| llm_context_relevance | 0.5081 | 0.5403 | ↑ +0.0323 |  |
| llm_faithfulness | 0.5860 | 0.5699 | ↓ -0.0161 |  |
| semantic_sim | 0.7905 | 0.7864 | ↓ -0.0041 |  |
| recall@3 | 0.6452 | 0.7258 | ↑ +0.0806 |  |
| recall@10 | 0.7581 | 0.7903 | ↑ +0.0323 |  |
| bertscore_f1 | 0.7529 | 0.7446 | ↓ -0.0083 |  |
| content_f1 | 0.2822 | 0.2621 | ↓ -0.0201 |  |
| citation_recall | 0.7581 | 0.7903 | ↑ +0.0323 |  |


### H1_BM25_ONLY_SYN

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.7581 | 0.5645 | ↓ -0.1935 | ** |
| ndcg@5 | 0.6727 | 0.5426 | ↓ -0.1301 | ** |
| mrr@5 | 0.7849 | 0.6543 | ↓ -0.1306 | *** |
| factual_consistency_normalized | 0.5081 | 0.5134 | ↑ +0.0054 |  |
| llm_answer_relevance | 0.5941 | 0.5887 | ↓ -0.0054 |  |
| llm_context_relevance | 0.5081 | 0.4677 | ↓ -0.0403 |  |
| llm_faithfulness | 0.5860 | 0.6129 | ↑ +0.0269 |  |
| semantic_sim | 0.7905 | 0.7523 | ↓ -0.0382 | * |
| recall@3 | 0.6452 | 0.5000 | ↓ -0.1452 | * |
| recall@10 | 0.7581 | 0.5645 | ↓ -0.1935 | ** |
| bertscore_f1 | 0.7529 | 0.7368 | ↓ -0.0161 |  |
| content_f1 | 0.2822 | 0.2404 | ↓ -0.0418 |  |
| citation_recall | 0.7581 | 0.5645 | ↓ -0.1935 | ** |


### H1_BM25_ONLY_SYN_RERANK

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.7581 | 0.7742 | ↑ +0.0161 |  |
| ndcg@5 | 0.6727 | 0.7153 | ↑ +0.0427 |  |
| mrr@5 | 0.7849 | 0.8226 | ↑ +0.0376 |  |
| factual_consistency_normalized | 0.5081 | 0.5027 | ↓ -0.0054 |  |
| llm_answer_relevance | 0.5941 | 0.6425 | ↑ +0.0484 |  |
| llm_context_relevance | 0.5081 | 0.5403 | ↑ +0.0323 |  |
| llm_faithfulness | 0.5860 | 0.5672 | ↓ -0.0188 |  |
| semantic_sim | 0.7905 | 0.7859 | ↓ -0.0047 |  |
| recall@3 | 0.6452 | 0.7097 | ↑ +0.0645 |  |
| recall@10 | 0.7581 | 0.7742 | ↑ +0.0161 |  |
| bertscore_f1 | 0.7529 | 0.7380 | ↓ -0.0149 | * |
| content_f1 | 0.2822 | 0.2486 | ↓ -0.0336 |  |
| citation_recall | 0.7581 | 0.7742 | ↑ +0.0161 |  |


---

*Report generiert am 2025-12-18 22:17:01*