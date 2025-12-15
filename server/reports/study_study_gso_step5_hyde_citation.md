# Study Report: study_gso_step5_hyde_citation

**Baseline:** ENHANCED_BASELINE
**Varianten:** 2
**Primäre Metriken:** recall@5, factual_consistency_normalized, semantic_sim

---

## Übersicht: Primäre Metriken

| Variante | recall@5 | factual_consistency_normalized | semantic_sim |
|----------|---:|---:|---:|
| **ENHANCED_BASELINE** (Baseline) | 0.7612 | 0.5185 | 0.8472 |
| GSO_S5_hyde (n=2) | 0.7402 ± 0.0396 (↓ -0.0211) | 0.5278 ± 0.0393 (↑ +0.0093) | 0.8354 ± 0.0086 (↓ -0.0118) |
| GSO_S5_citation_first (n=2) | 0.7612 (≈0) | 0.5069 ± 0.0098 (↓ -0.0116) | 0.8216 ± 0.0015 (↓ -0.0256*) |

*Signifikanz: *** p<0.001, ** p<0.01, * p<0.05*

## Ranking nach recall@5

1. **ENHANCED_BASELINE** (Baseline): 0.7612
2. **GSO_S5_citation_first**: 0.7612
3. **GSO_S5_hyde**: 0.7402

## Ranking nach factual_consistency_normalized

1. **GSO_S5_hyde**: 0.5278
2. **ENHANCED_BASELINE** (Baseline): 0.5185
3. **GSO_S5_citation_first**: 0.5069

## Ranking nach semantic_sim

1. **ENHANCED_BASELINE** (Baseline): 0.8472
2. **GSO_S5_hyde**: 0.8354
3. **GSO_S5_citation_first**: 0.8216


---

## Detailvergleiche

### GSO_S5_hyde

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.7612 | 0.7402 | ↓ -0.0211 |  |
| factual_consistency_normalized | 0.5185 | 0.5278 | ↑ +0.0093 |  |
| semantic_sim | 0.8472 | 0.8354 | ↓ -0.0118 |  |
| recall@3 | 0.6542 | 0.5985 | ↓ -0.0558 |  |
| recall@10 | 0.7612 | 0.7402 | ↓ -0.0211 |  |
| citation_recall | 0.7612 | 0.7402 | ↓ -0.0211 |  |


### GSO_S5_citation_first

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.7612 | 0.7612 | ≈0 |  |
| factual_consistency_normalized | 0.5185 | 0.5069 | ↓ -0.0116 |  |
| semantic_sim | 0.8472 | 0.8216 | ↓ -0.0256 | * |
| recall@3 | 0.6542 | 0.6542 | ≈0 |  |
| recall@10 | 0.7612 | 0.7612 | ≈0 |  |
| citation_recall | 0.7612 | 0.7612 | ≈0 |  |


---

*Report generiert am 2025-12-14 14:38:07*