# Study Report: study_gso_rerank_20_10

**Baseline:** OFAT_chunk_semantic_qwen3
**Varianten:** 2
**Primäre Metriken:** recall@5, factual_consistency_normalized, semantic_sim

---

## Übersicht: Primäre Metriken

| Variante | recall@5 | factual_consistency_normalized | semantic_sim |
|----------|---:|---:|---:|
| **OFAT_chunk_semantic_qwen3** (Baseline) | 0.7612 | 0.5556 | 0.8306 |
| GSO_S2_rerank_on_20 | 0.7631 (↑ +0.0019) | 0.5735 (↑ +0.0180) | 0.8316 (≈0) |
| GSO_S2_rerank_on_10 | 0.7492 (↓ -0.0120) | 0.5417 (↓ -0.0139) | 0.8318 (↑ +0.0012) |

*Signifikanz: *** p<0.001, ** p<0.01, * p<0.05*

## Ranking nach recall@5

1. **GSO_S2_rerank_on_20**: 0.7631
2. **OFAT_chunk_semantic_qwen3** (Baseline): 0.7612
3. **GSO_S2_rerank_on_10**: 0.7492

## Ranking nach factual_consistency_normalized

1. **GSO_S2_rerank_on_20**: 0.5735
2. **OFAT_chunk_semantic_qwen3** (Baseline): 0.5556
3. **GSO_S2_rerank_on_10**: 0.5417

## Ranking nach semantic_sim

1. **GSO_S2_rerank_on_10**: 0.8318
2. **GSO_S2_rerank_on_20**: 0.8316
3. **OFAT_chunk_semantic_qwen3** (Baseline): 0.8306


---

## Detailvergleiche

### GSO_S2_rerank_on_20

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.7612 | 0.7631 | ↑ +0.0019 |  |
| factual_consistency_normalized | 0.5556 | 0.5735 | ↑ +0.0180 |  |
| semantic_sim | 0.8306 | 0.8316 | ≈0 |  |
| recall@3 | 0.6542 | 0.6645 | ↑ +0.0103 |  |
| recall@10 | 0.7612 | 0.7631 | ↑ +0.0019 |  |
| citation_recall | 0.7612 | 0.7727 | ↑ +0.0114 |  |


### GSO_S2_rerank_on_10

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.7612 | 0.7492 | ↓ -0.0120 |  |
| factual_consistency_normalized | 0.5556 | 0.5417 | ↓ -0.0139 |  |
| semantic_sim | 0.8306 | 0.8318 | ↑ +0.0012 |  |
| recall@3 | 0.6542 | 0.6575 | ↑ +0.0033 |  |
| recall@10 | 0.7612 | 0.7492 | ↓ -0.0120 |  |
| citation_recall | 0.7612 | 0.7492 | ↓ -0.0120 |  |


---

*Report generiert am 2025-12-13 15:11:28*