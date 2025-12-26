# Study Report: study_quantization_q4_0

**Baseline:** ENHANCED_BASELINE
**Varianten:** 1
**Primäre Metriken:** recall@5, ndcg@5, factual_consistency_normalized, llm_answer_relevance, llm_faithfulness, semantic_sim

---

## Übersicht: Primäre Metriken

| Variante | recall@5 | ndcg@5 | factual_consistency_normalized | llm_answer_relevance | llm_faithfulness | semantic_sim |
|----------|---:|---:|---:|---:|---:|---:|
| **ENHANCED_BASELINE** (Baseline) | 0.7612 | 0.7700 | 0.5185 | 0.6435 | 0.6435 | 0.8472 |
| Q4_0_quantization | 0.7330 (↓ -0.0282) | 0.7887 (↑ +0.0187) | 0.5000 (↓ -0.0185) | 0.5694 (↓ -0.0741) | 0.5556 (↓ -0.0880) | 0.8594 (↑ +0.0122) |

*Signifikanz: *** p<0.001, ** p<0.01, * p<0.05*

## Ranking nach recall@5

1. **ENHANCED_BASELINE** (Baseline): 0.7612
2. **Q4_0_quantization**: 0.7330

## Ranking nach ndcg@5

1. **Q4_0_quantization**: 0.7887
2. **ENHANCED_BASELINE** (Baseline): 0.7700

## Ranking nach factual_consistency_normalized

1. **ENHANCED_BASELINE** (Baseline): 0.5185
2. **Q4_0_quantization**: 0.5000

## Ranking nach llm_answer_relevance

1. **ENHANCED_BASELINE** (Baseline): 0.6435
2. **Q4_0_quantization**: 0.5694

## Ranking nach llm_faithfulness

1. **ENHANCED_BASELINE** (Baseline): 0.6435
2. **Q4_0_quantization**: 0.5556

## Ranking nach semantic_sim

1. **Q4_0_quantization**: 0.8594
2. **ENHANCED_BASELINE** (Baseline): 0.8472


---

## Detailvergleiche

### Q4_0_quantization

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.7612 | 0.7330 | ↓ -0.0282 |  |
| ndcg@5 | 0.7700 | 0.7887 | ↑ +0.0187 |  |
| factual_consistency_normalized | 0.5185 | 0.5000 | ↓ -0.0185 |  |
| llm_answer_relevance | 0.6435 | 0.5694 | ↓ -0.0741 |  |
| llm_faithfulness | 0.6435 | 0.5556 | ↓ -0.0880 |  |
| semantic_sim | 0.8472 | 0.8594 | ↑ +0.0122 |  |
| bertscore_f1 | 0.7490 | 0.7469 | ↓ -0.0022 |  |
| content_f1 | 0.3182 | 0.3128 | ↓ -0.0054 |  |


---

*Report generiert am 2025-12-26 17:09:50*