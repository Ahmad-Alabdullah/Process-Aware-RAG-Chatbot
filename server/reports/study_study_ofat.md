# Study Report: study_ofat

**Baseline:** BASELINE
**Varianten:** 1
**Primäre Metriken:** recall@5, ndcg@5, factual_consistency_normalized, semantic_sim

---

## Übersicht: Primäre Metriken

| Variante | recall@5 | ndcg@5 | factual_consistency_normalized | semantic_sim |
|----------|---:|---:|---:|---:|
| **BASELINE** (Baseline) | 0.6597 | 0.6664 | 0.5147 | 0.8449 |
| OFAT_prompt_structured | 0.6597 (≈0) | 0.6664 (≈0) | 0.5000 (↓ -0.0147) | 0.8558 (↑ +0.0109*) |

*Signifikanz: *** p<0.001, ** p<0.01, * p<0.05*

## Ranking nach recall@5

1. **BASELINE** (Baseline): 0.6597
2. **OFAT_prompt_structured**: 0.6597

---

## Detailvergleiche

### OFAT_prompt_structured

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.6597 | 0.6597 | ≈0 |  |
| ndcg@5 | 0.6664 | 0.6664 | ≈0 |  |
| factual_consistency_normalized | 0.5147 | 0.5000 | ↓ -0.0147 |  |
| semantic_sim | 0.8449 | 0.8558 | ↑ +0.0109 | * |
| recall@3 | 0.5421 | 0.5421 | ≈0 |  |
| recall@10 | 0.6597 | 0.6597 | ≈0 |  |
| citation_recall | 0.6515 | 0.6778 | ↑ +0.0263 |  |


---

*Report generiert am 2025-12-10 15:09:12*