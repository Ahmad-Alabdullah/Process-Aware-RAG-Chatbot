# Study Report: study_ofat

**Baseline:** BASELINE
**Varianten:** 14
**Primäre Metriken:** recall@5, ndcg@5, factual_consistency_normalized, llm_answer_relevance, llm_context_relevance, llm_faithfulness, semantic_sim

---

## Übersicht: Primäre Metriken

| Variante | recall@5 | ndcg@5 | factual_consistency_normalized | llm_answer_relevance | llm_context_relevance | llm_faithfulness | semantic_sim |
|----------|---:|---:|---:|---:|---:|---:|---:|
| **BASELINE** (Baseline) | 0.6597 | 0.6664 | 0.5156 | 0.6250 | 0.5625 | 0.6250 | 0.8302 |
| OFAT_temp_0.0 | 0.6597 (≈0) | 0.6664 (≈0) | 0.5000 (↓ -0.0156) | 0.5882 (↓ -0.0368) | 0.5441 (↓ -0.0184) | 0.5588 (↓ -0.0662) | 0.8420 (↑ +0.0119) |
| OFAT_embed_qwen3_bytitle | 0.7218 (↑ +0.0620) | 0.7340 (↑ +0.0676) | 0.5294 (↑ +0.0138) | 0.6176 (↓ -0.0074) | 0.5588 (↓ -0.0037) | 0.6471 (↑ +0.0221) | 0.8380 (↑ +0.0078) |
| OFAT_chunk_semantic_minilm | 0.6098 (↓ -0.0499) | 0.4368 (↓ -0.2296***) | 0.5000 (↓ -0.0156) | 0.6389 (↑ +0.0139) | 0.5139 (↓ -0.0486) | 0.5556 (↓ -0.0694) | 0.8182 (↓ -0.0120) |
| OFAT_chunk_semantic_qwen3 | 0.7612 (↑ +0.1015*) | 0.7700 (↑ +0.1037) | 0.5556 (↑ +0.0399) | 0.6111 (↓ -0.0139) | 0.5833 (↑ +0.0208) | 0.6111 (↓ -0.0139) | 0.8306 (≈0) |
| OFAT_prompt_structured | 0.6597 (≈0) | 0.6664 (≈0) | 0.5000 (↓ -0.0156) | 0.5294 (↓ -0.0956) | 0.5441 (↓ -0.0184) | 0.6471 (↑ +0.0221) | 0.8522 (↑ +0.0220) |
| OFAT_temp_0.3 | 0.6597 (≈0) | 0.6664 (≈0) | 0.5000 (↓ -0.0156) | 0.6389 (↑ +0.0139) | 0.5556 (↓ -0.0069) | 0.5556 (↓ -0.0694) | 0.8356 (↑ +0.0054) |
| OFAT_qwen3:8b-q4_K_M | 0.6597 (≈0) | 0.6664 (≈0) | 0.5278 (↑ +0.0122) | 0.6111 (↓ -0.0139) | 0.5556 (↓ -0.0069) | 0.5417 (↓ -0.0833*) | 0.8276 (↓ -0.0026) |
| OFAT_llm_llama3.1:8b | 0.6597 (≈0) | 0.6664 (≈0) | 0.5139 (↓ -0.0017) | 0.6528 (↑ +0.0278) | 0.5556 (↓ -0.0069) | 0.5556 (↓ -0.0694) | 0.8324 (↑ +0.0022) |
| OFAT_llm_llama3.1:8b-instruct-q4_K_M | 0.6597 (≈0) | 0.6664 (≈0) | 0.5139 (↓ -0.0017) | 0.5139 (↓ -0.1111) | 0.5556 (↓ -0.0069) | 0.5694 (↓ -0.0556) | 0.8472 (↑ +0.0170) |
| OFAT_k3 | 0.5347 (↓ -0.1250***) | 0.5875 (↓ -0.0789*) | 0.5000 (↓ -0.0156) | 0.5556 (↓ -0.0694) | 0.5556 (↓ -0.0069) | 0.5972 (↓ -0.0278) | 0.8305 (≈0) |
| OFAT_k10 | 0.6542 (↓ -0.0056) | 0.6608 (↓ -0.0056) | 0.5469 (↑ +0.0312) | 0.6250 (≈0) | 0.5469 (↓ -0.0156) | 0.6250 (≈0) | 0.8393 (↑ +0.0091) |
| OFAT_rerank_on | 0.1815 (↓ -0.4782***) | 0.1229 (↓ -0.5435***) | 0.5000 (↓ -0.0156) | 0.5441 (↓ -0.0809) | 0.4559 (↓ -0.1066**) | 0.5735 (↓ -0.0515) | 0.7976 (↓ -0.0326) |
| OFAT_prompt_fewshot | 0.6597 (≈0) | 0.6664 (≈0) | 0.5000 (↓ -0.0156) | 0.6111 (↓ -0.0139) | 0.5556 (↓ -0.0069) | 0.6111 (↓ -0.0139) | 0.8456 (↑ +0.0154) |
| OFAT_prompt_cot | 0.6597 (≈0) | 0.6664 (≈0) | 0.5139 (↓ -0.0017) | 0.5972 (↓ -0.0278) | 0.5556 (↓ -0.0069) | 0.6528 (↑ +0.0278) | 0.8366 (↑ +0.0064) |

*Signifikanz: *** p<0.001, ** p<0.01, * p<0.05*

## Ranking nach recall@5

1. **OFAT_chunk_semantic_qwen3**: 0.7612
2. **OFAT_embed_qwen3_bytitle**: 0.7218
3. **BASELINE** (Baseline): 0.6597
4. **OFAT_temp_0.0**: 0.6597
5. **OFAT_prompt_structured**: 0.6597
6. **OFAT_temp_0.3**: 0.6597
7. **OFAT_qwen3:8b-q4_K_M**: 0.6597
8. **OFAT_llm_llama3.1:8b**: 0.6597
9. **OFAT_llm_llama3.1:8b-instruct-q4_K_M**: 0.6597
10. **OFAT_prompt_fewshot**: 0.6597
11. **OFAT_prompt_cot**: 0.6597
12. **OFAT_k10**: 0.6542
13. **OFAT_chunk_semantic_minilm**: 0.6098
14. **OFAT_k3**: 0.5347
15. **OFAT_rerank_on**: 0.1815

---

## Detailvergleiche

### OFAT_temp_0.0

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.6597 | 0.6597 | ≈0 |  |
| ndcg@5 | 0.6664 | 0.6664 | ≈0 |  |
| factual_consistency_normalized | 0.5156 | 0.5000 | ↓ -0.0156 |  |
| llm_answer_relevance | 0.6250 | 0.5882 | ↓ -0.0368 |  |
| llm_context_relevance | 0.5625 | 0.5441 | ↓ -0.0184 |  |
| llm_faithfulness | 0.6250 | 0.5588 | ↓ -0.0662 |  |
| semantic_sim | 0.8302 | 0.8420 | ↑ +0.0119 |  |
| recall@3 | 0.5421 | 0.5421 | ≈0 |  |
| recall@10 | 0.6597 | 0.6597 | ≈0 |  |
| citation_recall | 0.6714 | 0.6515 | ↓ -0.0199 |  |


### OFAT_embed_qwen3_bytitle

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.6597 | 0.7218 | ↑ +0.0620 |  |
| ndcg@5 | 0.6664 | 0.7340 | ↑ +0.0676 |  |
| factual_consistency_normalized | 0.5156 | 0.5294 | ↑ +0.0138 |  |
| llm_answer_relevance | 0.6250 | 0.6176 | ↓ -0.0074 |  |
| llm_context_relevance | 0.5625 | 0.5588 | ↓ -0.0037 |  |
| llm_faithfulness | 0.6250 | 0.6471 | ↑ +0.0221 |  |
| semantic_sim | 0.8302 | 0.8380 | ↑ +0.0078 |  |
| recall@3 | 0.5421 | 0.6329 | ↑ +0.0907 | ** |
| recall@10 | 0.6597 | 0.7218 | ↑ +0.0620 |  |
| citation_recall | 0.6714 | 0.7172 | ↑ +0.0458 |  |


### OFAT_chunk_semantic_minilm

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.6597 | 0.6098 | ↓ -0.0499 |  |
| ndcg@5 | 0.6664 | 0.4368 | ↓ -0.2296 | *** |
| factual_consistency_normalized | 0.5156 | 0.5000 | ↓ -0.0156 |  |
| llm_answer_relevance | 0.6250 | 0.6389 | ↑ +0.0139 |  |
| llm_context_relevance | 0.5625 | 0.5139 | ↓ -0.0486 |  |
| llm_faithfulness | 0.6250 | 0.5556 | ↓ -0.0694 |  |
| semantic_sim | 0.8302 | 0.8182 | ↓ -0.0120 |  |
| recall@3 | 0.5421 | 0.4515 | ↓ -0.0907 | * |
| recall@10 | 0.6597 | 0.6098 | ↓ -0.0499 |  |
| citation_recall | 0.6714 | 0.6098 | ↓ -0.0616 |  |


### OFAT_chunk_semantic_qwen3

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.6597 | 0.7612 | ↑ +0.1015 | * |
| ndcg@5 | 0.6664 | 0.7700 | ↑ +0.1037 |  |
| factual_consistency_normalized | 0.5156 | 0.5556 | ↑ +0.0399 |  |
| llm_answer_relevance | 0.6250 | 0.6111 | ↓ -0.0139 |  |
| llm_context_relevance | 0.5625 | 0.5833 | ↑ +0.0208 |  |
| llm_faithfulness | 0.6250 | 0.6111 | ↓ -0.0139 |  |
| semantic_sim | 0.8302 | 0.8306 | ≈0 |  |
| recall@3 | 0.5421 | 0.6542 | ↑ +0.1121 | ** |
| recall@10 | 0.6597 | 0.7612 | ↑ +0.1015 | * |
| citation_recall | 0.6714 | 0.7612 | ↑ +0.0899 | * |


### OFAT_prompt_structured

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.6597 | 0.6597 | ≈0 |  |
| ndcg@5 | 0.6664 | 0.6664 | ≈0 |  |
| factual_consistency_normalized | 0.5156 | 0.5000 | ↓ -0.0156 |  |
| llm_answer_relevance | 0.6250 | 0.5294 | ↓ -0.0956 |  |
| llm_context_relevance | 0.5625 | 0.5441 | ↓ -0.0184 |  |
| llm_faithfulness | 0.6250 | 0.6471 | ↑ +0.0221 |  |
| semantic_sim | 0.8302 | 0.8522 | ↑ +0.0220 |  |
| recall@3 | 0.5421 | 0.5421 | ≈0 |  |
| recall@10 | 0.6597 | 0.6597 | ≈0 |  |
| citation_recall | 0.6714 | 0.6515 | ↓ -0.0199 |  |


### OFAT_temp_0.3

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.6597 | 0.6597 | ≈0 |  |
| ndcg@5 | 0.6664 | 0.6664 | ≈0 |  |
| factual_consistency_normalized | 0.5156 | 0.5000 | ↓ -0.0156 |  |
| llm_answer_relevance | 0.6250 | 0.6389 | ↑ +0.0139 |  |
| llm_context_relevance | 0.5625 | 0.5556 | ↓ -0.0069 |  |
| llm_faithfulness | 0.6250 | 0.5556 | ↓ -0.0694 |  |
| semantic_sim | 0.8302 | 0.8356 | ↑ +0.0054 |  |
| recall@3 | 0.5421 | 0.5421 | ≈0 |  |
| recall@10 | 0.6597 | 0.6597 | ≈0 |  |
| citation_recall | 0.6714 | 0.6597 | ↓ -0.0116 |  |


### OFAT_qwen3:8b-q4_K_M

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.6597 | 0.6597 | ≈0 |  |
| ndcg@5 | 0.6664 | 0.6664 | ≈0 |  |
| factual_consistency_normalized | 0.5156 | 0.5278 | ↑ +0.0122 |  |
| llm_answer_relevance | 0.6250 | 0.6111 | ↓ -0.0139 |  |
| llm_context_relevance | 0.5625 | 0.5556 | ↓ -0.0069 |  |
| llm_faithfulness | 0.6250 | 0.5417 | ↓ -0.0833 | * |
| semantic_sim | 0.8302 | 0.8276 | ↓ -0.0026 |  |
| recall@3 | 0.5421 | 0.5421 | ≈0 |  |
| recall@10 | 0.6597 | 0.6597 | ≈0 |  |
| citation_recall | 0.6714 | 0.6597 | ↓ -0.0116 |  |


### OFAT_llm_llama3.1:8b

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.6597 | 0.6597 | ≈0 |  |
| ndcg@5 | 0.6664 | 0.6664 | ≈0 |  |
| factual_consistency_normalized | 0.5156 | 0.5139 | ↓ -0.0017 |  |
| llm_answer_relevance | 0.6250 | 0.6528 | ↑ +0.0278 |  |
| llm_context_relevance | 0.5625 | 0.5556 | ↓ -0.0069 |  |
| llm_faithfulness | 0.6250 | 0.5556 | ↓ -0.0694 |  |
| semantic_sim | 0.8302 | 0.8324 | ↑ +0.0022 |  |
| recall@3 | 0.5421 | 0.5421 | ≈0 |  |
| recall@10 | 0.6597 | 0.6597 | ≈0 |  |
| citation_recall | 0.6714 | 0.6597 | ↓ -0.0116 |  |


### OFAT_llm_llama3.1:8b-instruct-q4_K_M

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.6597 | 0.6597 | ≈0 |  |
| ndcg@5 | 0.6664 | 0.6664 | ≈0 |  |
| factual_consistency_normalized | 0.5156 | 0.5139 | ↓ -0.0017 |  |
| llm_answer_relevance | 0.6250 | 0.5139 | ↓ -0.1111 |  |
| llm_context_relevance | 0.5625 | 0.5556 | ↓ -0.0069 |  |
| llm_faithfulness | 0.6250 | 0.5694 | ↓ -0.0556 |  |
| semantic_sim | 0.8302 | 0.8472 | ↑ +0.0170 |  |
| recall@3 | 0.5421 | 0.5421 | ≈0 |  |
| recall@10 | 0.6597 | 0.6597 | ≈0 |  |
| citation_recall | 0.6714 | 0.6597 | ↓ -0.0116 |  |


### OFAT_k3

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.6597 | 0.5347 | ↓ -0.1250 | *** |
| ndcg@5 | 0.6664 | 0.5875 | ↓ -0.0789 | * |
| factual_consistency_normalized | 0.5156 | 0.5000 | ↓ -0.0156 |  |
| llm_answer_relevance | 0.6250 | 0.5556 | ↓ -0.0694 |  |
| llm_context_relevance | 0.5625 | 0.5556 | ↓ -0.0069 |  |
| llm_faithfulness | 0.6250 | 0.5972 | ↓ -0.0278 |  |
| semantic_sim | 0.8302 | 0.8305 | ≈0 |  |
| recall@3 | 0.5421 | 0.5347 | ↓ -0.0074 |  |
| recall@10 | 0.6597 | 0.5347 | ↓ -0.1250 | *** |
| citation_recall | 0.6714 | 0.5347 | ↓ -0.1366 | ** |


### OFAT_k10

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.6597 | 0.6542 | ↓ -0.0056 |  |
| ndcg@5 | 0.6664 | 0.6608 | ↓ -0.0056 |  |
| factual_consistency_normalized | 0.5156 | 0.5469 | ↑ +0.0312 |  |
| llm_answer_relevance | 0.6250 | 0.6250 | ≈0 |  |
| llm_context_relevance | 0.5625 | 0.5469 | ↓ -0.0156 |  |
| llm_faithfulness | 0.6250 | 0.6250 | ≈0 |  |
| semantic_sim | 0.8302 | 0.8393 | ↑ +0.0091 |  |
| recall@3 | 0.5421 | 0.5421 | ≈0 |  |
| recall@10 | 0.6597 | 0.8296 | ↑ +0.1699 | *** |
| citation_recall | 0.6714 | 0.8083 | ↑ +0.1370 | ** |


### OFAT_rerank_on

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.6597 | 0.1815 | ↓ -0.4782 | *** |
| ndcg@5 | 0.6664 | 0.1229 | ↓ -0.5435 | *** |
| factual_consistency_normalized | 0.5156 | 0.5000 | ↓ -0.0156 |  |
| llm_answer_relevance | 0.6250 | 0.5441 | ↓ -0.0809 |  |
| llm_context_relevance | 0.5625 | 0.4559 | ↓ -0.1066 | ** |
| llm_faithfulness | 0.6250 | 0.5735 | ↓ -0.0515 |  |
| semantic_sim | 0.8302 | 0.7976 | ↓ -0.0326 |  |
| recall@3 | 0.5421 | 0.0926 | ↓ -0.4495 | *** |
| recall@10 | 0.6597 | 0.1815 | ↓ -0.4782 | *** |
| citation_recall | 0.6714 | 0.1569 | ↓ -0.5145 | *** |


### OFAT_prompt_fewshot

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.6597 | 0.6597 | ≈0 |  |
| ndcg@5 | 0.6664 | 0.6664 | ≈0 |  |
| factual_consistency_normalized | 0.5156 | 0.5000 | ↓ -0.0156 |  |
| llm_answer_relevance | 0.6250 | 0.6111 | ↓ -0.0139 |  |
| llm_context_relevance | 0.5625 | 0.5556 | ↓ -0.0069 |  |
| llm_faithfulness | 0.6250 | 0.6111 | ↓ -0.0139 |  |
| semantic_sim | 0.8302 | 0.8456 | ↑ +0.0154 |  |
| recall@3 | 0.5421 | 0.5421 | ≈0 |  |
| recall@10 | 0.6597 | 0.6597 | ≈0 |  |
| citation_recall | 0.6714 | 0.6597 | ↓ -0.0116 |  |


### OFAT_prompt_cot

| Metrik | Baseline | Variante | Δ | Sig |
|--------|--------:|--------:|---:|:---:|
| recall@5 | 0.6597 | 0.6597 | ≈0 |  |
| ndcg@5 | 0.6664 | 0.6664 | ≈0 |  |
| factual_consistency_normalized | 0.5156 | 0.5139 | ↓ -0.0017 |  |
| llm_answer_relevance | 0.6250 | 0.5972 | ↓ -0.0278 |  |
| llm_context_relevance | 0.5625 | 0.5556 | ↓ -0.0069 |  |
| llm_faithfulness | 0.6250 | 0.6528 | ↑ +0.0278 |  |
| semantic_sim | 0.8302 | 0.8366 | ↑ +0.0064 |  |
| recall@3 | 0.5421 | 0.5421 | ≈0 |  |
| recall@10 | 0.6597 | 0.6597 | ≈0 |  |
| citation_recall | 0.6714 | 0.6597 | ↓ -0.0116 |  |


---

*Report generiert am 2025-12-11 18:23:33*