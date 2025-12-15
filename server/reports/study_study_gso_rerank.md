# Study Report: study_gso_rerank

**Baseline:** OFAT_chunk_semantic_qwen3
**Varianten:** 1
**Primäre Metriken:** recall@5, factual_consistency_normalized, semantic_sim

---

## Übersicht: Primäre Metriken

| Variante | recall@5 | factual_consistency_normalized | semantic_sim |
|----------|---:|---:|---:|
| **OFAT_chunk_semantic_qwen3** (Baseline) | 0.7612 | 0.5556 | 0.8306 |
| GSO_S2_rerank_on | 0.7631 (↑ +0.0019) | 0.5156 (↓ -0.0399) | 0.8242 (↓ -0.0064) |

*Signifikanz: *** p<0.001, ** p<0.01, * p<0.05*

## Ranking nach recall@5

1. **GSO_S2_rerank_on**: 0.7631
2. **OFAT_chunk_semantic_qwen3** (Baseline): 0.7612

## Ranking nach factual_consistency_normalized

1. **OFAT_chunk_semantic_qwen3** (Baseline): 0.5556
2. **GSO_S2_rerank_on**: 0.5156

## Ranking nach semantic_sim

1. **OFAT_chunk_semantic_qwen3** (Baseline): 0.8306
2. **GSO_S2_rerank_on**: 0.8242


---

## Detailvergleiche

### GSO_S2_rerank_on

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.7612 | 0.7631 | ↑ +0.0019 |  |
| factual_consistency_normalized | 0.5556 | 0.5156 | ↓ -0.0399 |  |
| semantic_sim | 0.8306 | 0.8242 | ↓ -0.0064 |  |
| recall@3 | 0.6542 | 0.6645 | ↑ +0.0103 |  |
| recall@10 | 0.7612 | 0.7631 | ↑ +0.0019 |  |
| citation_recall | 0.7612 | 0.8031 | ↑ +0.0419 |  |


---

*Report generiert am 2025-12-13 14:33:31*