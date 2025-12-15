# Study Report: study_gso_llm_prompt

**Baseline:** OFAT_chunk_semantic_qwen3
**Varianten:** 5
**Primäre Metriken:** recall@5, factual_consistency_normalized, semantic_sim

---

## Übersicht: Primäre Metriken

| Variante | recall@5 | factual_consistency_normalized | semantic_sim |
|----------|---:|---:|---:|
| **OFAT_chunk_semantic_qwen3** (Baseline) | 0.7612 | 0.5556 | 0.8306 |
| GSO_S3_deepseek-r1:8b | 0.7612 (≈0) | 0.5000 (↓ -0.0556) | 0.8346 (↑ +0.0039) |
| GSO_S3_deepseek-r1:7b | 0.7612 (≈0) | 0.5000 (↓ -0.0556) | 0.7980 (↓ -0.0326*) |
| GSO_S3_llama31 | 0.7612 (≈0) | 0.5000 (↓ -0.0556) | 0.8660 (↑ +0.0354***) |
| GSO_S3_qwen2_5 | 0.7612 (≈0) | 0.5417 (↓ -0.0139) | 0.8468 (↑ +0.0162) |
| GSO_S3_cot | 0.7612 (≈0) | 0.5735 (↑ +0.0180) | 0.8389 (↑ +0.0083) |

*Signifikanz: *** p<0.001, ** p<0.01, * p<0.05*

## Ranking nach recall@5

1. **OFAT_chunk_semantic_qwen3** (Baseline): 0.7612
2. **GSO_S3_deepseek-r1:8b**: 0.7612
3. **GSO_S3_deepseek-r1:7b**: 0.7612
4. **GSO_S3_llama31**: 0.7612
5. **GSO_S3_qwen2_5**: 0.7612
6. **GSO_S3_cot**: 0.7612

## Ranking nach factual_consistency_normalized

1. **GSO_S3_cot**: 0.5735
2. **OFAT_chunk_semantic_qwen3** (Baseline): 0.5556
3. **GSO_S3_qwen2_5**: 0.5417
4. **GSO_S3_deepseek-r1:8b**: 0.5000
5. **GSO_S3_deepseek-r1:7b**: 0.5000
6. **GSO_S3_llama31**: 0.5000

## Ranking nach semantic_sim

1. **GSO_S3_llama31**: 0.8660
2. **GSO_S3_qwen2_5**: 0.8468
3. **GSO_S3_cot**: 0.8389
4. **GSO_S3_deepseek-r1:8b**: 0.8346
5. **OFAT_chunk_semantic_qwen3** (Baseline): 0.8306
6. **GSO_S3_deepseek-r1:7b**: 0.7980


---

## Detailvergleiche

### GSO_S3_deepseek-r1:8b

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.7612 | 0.7612 | ≈0 |  |
| factual_consistency_normalized | 0.5556 | 0.5000 | ↓ -0.0556 |  |
| semantic_sim | 0.8306 | 0.8346 | ↑ +0.0039 |  |
| recall@3 | 0.6542 | 0.6542 | ≈0 |  |
| recall@10 | 0.7612 | 0.7612 | ≈0 |  |
| citation_recall | 0.7612 | 0.7707 | ↑ +0.0095 |  |


### GSO_S3_deepseek-r1:7b

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.7612 | 0.7612 | ≈0 |  |
| factual_consistency_normalized | 0.5556 | 0.5000 | ↓ -0.0556 |  |
| semantic_sim | 0.8306 | 0.7980 | ↓ -0.0326 | * |
| recall@3 | 0.6542 | 0.6542 | ≈0 |  |
| recall@10 | 0.7612 | 0.7612 | ≈0 |  |
| citation_recall | 0.7612 | 0.7612 | ≈0 |  |


### GSO_S3_llama31

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.7612 | 0.7612 | ≈0 |  |
| factual_consistency_normalized | 0.5556 | 0.5000 | ↓ -0.0556 |  |
| semantic_sim | 0.8306 | 0.8660 | ↑ +0.0354 | *** |
| recall@3 | 0.6542 | 0.6542 | ≈0 |  |
| recall@10 | 0.7612 | 0.7612 | ≈0 |  |
| citation_recall | 0.7612 | 0.7612 | ≈0 |  |


### GSO_S3_qwen2_5

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.7612 | 0.7612 | ≈0 |  |
| factual_consistency_normalized | 0.5556 | 0.5417 | ↓ -0.0139 |  |
| semantic_sim | 0.8306 | 0.8468 | ↑ +0.0162 |  |
| recall@3 | 0.6542 | 0.6542 | ≈0 |  |
| recall@10 | 0.7612 | 0.7612 | ≈0 |  |
| citation_recall | 0.7612 | 0.7612 | ≈0 |  |


### GSO_S3_cot

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.7612 | 0.7612 | ≈0 |  |
| factual_consistency_normalized | 0.5556 | 0.5735 | ↑ +0.0180 |  |
| semantic_sim | 0.8306 | 0.8389 | ↑ +0.0083 |  |
| recall@3 | 0.6542 | 0.6542 | ≈0 |  |
| recall@10 | 0.7612 | 0.7612 | ≈0 |  |
| citation_recall | 0.7612 | 0.7707 | ↑ +0.0095 |  |


---

*Report generiert am 2025-12-13 16:53:43*