# Study Report: study_gso

**Baseline:** OFAT_chunk_semantic_qwen3
**Varianten:** 2
**Primäre Metriken:** recall@5, factual_consistency_normalized, semantic_sim

---

## Übersicht: Primäre Metriken

| Variante | recall@5 | factual_consistency_normalized | semantic_sim |
|----------|---:|---:|---:|
| **OFAT_chunk_semantic_qwen3** (Baseline) | 0.7612 | 0.5556 | 0.8306 |
| GSO_S1_k10 | 0.7612 (≈0) | 0.5000 (↓ -0.0556) | 0.8321 (↑ +0.0015) |
| GSO_S1_k15 | 0.7612 (≈0) | 0.5333 (↓ -0.0222) | 0.8308 (≈0) |

*Signifikanz: *** p<0.001, ** p<0.01, * p<0.05*

## Ranking nach recall@5

1. **OFAT_chunk_semantic_qwen3** (Baseline): 0.7612
2. **GSO_S1_k10**: 0.7612
3. **GSO_S1_k15**: 0.7612

## Ranking nach factual_consistency_normalized

1. **OFAT_chunk_semantic_qwen3** (Baseline): 0.5556
2. **GSO_S1_k15**: 0.5333
3. **GSO_S1_k10**: 0.5000

## Ranking nach semantic_sim

1. **GSO_S1_k10**: 0.8321
2. **GSO_S1_k15**: 0.8308
3. **OFAT_chunk_semantic_qwen3** (Baseline): 0.8306


---

## Detailvergleiche

### GSO_S1_k10

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.7612 | 0.7612 | ≈0 |  |
| factual_consistency_normalized | 0.5556 | 0.5000 | ↓ -0.0556 |  |
| semantic_sim | 0.8306 | 0.8321 | ↑ +0.0015 |  |
| recall@3 | 0.6542 | 0.6542 | ≈0 |  |
| recall@10 | 0.7612 | 0.9127 | ↑ +0.1515 | *** |
| citation_recall | 0.7612 | 0.9076 | ↑ +0.1463 | ** |


### GSO_S1_k15

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.7612 | 0.7612 | ≈0 |  |
| factual_consistency_normalized | 0.5556 | 0.5333 | ↓ -0.0222 |  |
| semantic_sim | 0.8306 | 0.8308 | ≈0 |  |
| recall@3 | 0.6542 | 0.6542 | ≈0 |  |
| recall@10 | 0.7612 | 0.9127 | ↑ +0.1515 | *** |
| citation_recall | 0.7612 | 0.9750 | ↑ +0.2138 | ** |


---

*Report generiert am 2025-12-11 20:25:13*