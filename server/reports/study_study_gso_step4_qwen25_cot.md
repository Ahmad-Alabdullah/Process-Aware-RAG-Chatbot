# Study Report: study_gso_step4_qwen25_cot

**Baseline:** OFAT_chunk_semantic_qwen3
**Varianten:** 1
**Primäre Metriken:** recall@5, factual_consistency_normalized, semantic_sim

---

## Übersicht: Primäre Metriken

| Variante | recall@5 | factual_consistency_normalized | semantic_sim |
|----------|---:|---:|---:|
| **OFAT_chunk_semantic_qwen3** (Baseline) | 0.7612 | 0.5556 | 0.8306 |
| GSO_S4_qwen25_cot | 0.7612 (≈0) | 0.5278 (↓ -0.0278) | 0.8394 (↑ +0.0088) |

*Signifikanz: *** p<0.001, ** p<0.01, * p<0.05*

## Ranking nach recall@5

1. **OFAT_chunk_semantic_qwen3** (Baseline): 0.7612
2. **GSO_S4_qwen25_cot**: 0.7612

## Ranking nach factual_consistency_normalized

1. **OFAT_chunk_semantic_qwen3** (Baseline): 0.5556
2. **GSO_S4_qwen25_cot**: 0.5278

## Ranking nach semantic_sim

1. **GSO_S4_qwen25_cot**: 0.8394
2. **OFAT_chunk_semantic_qwen3** (Baseline): 0.8306


---

## Detailvergleiche

### GSO_S4_qwen25_cot

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.7612 | 0.7612 | ≈0 |  |
| factual_consistency_normalized | 0.5556 | 0.5278 | ↓ -0.0278 |  |
| semantic_sim | 0.8306 | 0.8394 | ↑ +0.0088 |  |
| recall@3 | 0.6542 | 0.6542 | ≈0 |  |
| recall@10 | 0.7612 | 0.7612 | ≈0 |  |
| citation_recall | 0.7612 | 0.7612 | ≈0 |  |


---

*Report generiert am 2025-12-13 17:13:23*