from __future__ import annotations
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class LLMTaskConfig(BaseModel):
    """LLM-Konfiguration für einen spezifischen Task."""

    model: str = Field(default="qwen3:8b")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1)
    num_ctx: int = Field(default=8192, ge=512)


class LLMFactorsConfig(BaseModel):
    """LLM-Konfigurationen für verschiedene Tasks."""

    qa: LLMTaskConfig = Field(default_factory=lambda: LLMTaskConfig(temperature=0.1))
    hyde: LLMTaskConfig = Field(
        default_factory=lambda: LLMTaskConfig(temperature=0.3, max_tokens=512)
    )
    cot: LLMTaskConfig = Field(
        default_factory=lambda: LLMTaskConfig(temperature=0.2, max_tokens=3072)
    )


class EmbeddingConfig(BaseModel):
    """Embedding-Konfiguration für Retrieval."""

    backend: str = Field(default="ollama", description="'ollama' oder 'hf'")
    model: str = Field(default="qwen3-embedding:4b", description="Modellname")
    index_suffix: str = Field(default="", description="Suffix für OS/Qdrant Index")


class RerankConfig(BaseModel):
    """Reranking-Konfiguration."""

    enabled: bool = Field(default=False)
    model: str = Field(default="jina-reranker-v3")
    top_n: int = Field(default=50)


class EvaluationConfig(BaseModel):
    """Evaluation-Konfiguration."""

    use_llm_judge: bool = Field(default=True)
    judge_model: str = Field(default="atla/selene-mini")
    semantic_sim_model: str = Field(default="EmbeddingGemma:300m")
    bertscore_model: str = Field(default="deepset/gbert-large")


class ChunkingConfig(BaseModel):
    """Chunking-Konfiguration."""

    max_characters: int = Field(default=1800)
    new_after_n_chars: int = Field(default=1350)
    overlap: int = Field(default=225)
    strategy: str = Field(default="by_title", description="'by_title' oder 'semantic'")

    def get_qrels_suffix(self) -> str:
        """Gibt den Suffix für die Qrels-Datei zurück."""
        if self.strategy == "semantic":
            return "semantic"
        else:
            return "1800"  # Default für by_title


class RunConfig(BaseModel):
    run_name: str
    dataset: str
    qa_base_url: str
    qa_payload: Dict[str, Any] = Field(default_factory=dict)
    factors: Dict[str, Any] = Field(default_factory=dict)
    logging: Dict[str, Any] = Field(default_factory=dict)
    ranking_sources: List[str] = Field(default_factory=lambda: ["ce", "rrf"])
    ranking_fallback_all: bool = Field(default=True)

    def get_embedding_config(self) -> EmbeddingConfig:
        """Extrahiert Embedding-Konfiguration aus factors."""
        emb_cfg = self.factors.get("embeddings", {})
        return (
            EmbeddingConfig(**emb_cfg)
            if isinstance(emb_cfg, dict)
            else EmbeddingConfig()
        )

    def get_rerank_config(self) -> RerankConfig:
        """Extrahiert Rerank-Konfiguration aus factors."""
        rerank_cfg = self.factors.get("rerank", {})
        return (
            RerankConfig(**rerank_cfg)
            if isinstance(rerank_cfg, dict)
            else RerankConfig()
        )

    def get_evaluation_config(self) -> EvaluationConfig:
        """Extrahiert Evaluation-Konfiguration aus factors."""
        eval_cfg = self.factors.get("evaluation", {})
        return (
            EvaluationConfig(**eval_cfg)
            if isinstance(eval_cfg, dict)
            else EvaluationConfig()
        )

    def get_llm_config(self, task: str = "qa") -> LLMTaskConfig:
        """
        Extrahiert LLM-Konfiguration für einen spezifischen Task.

        Args:
            task: "qa", "hyde", oder "cot"
        """
        llm_cfg = self.factors.get("llm", {})
        task_cfg = llm_cfg.get(task, {})

        # Defaults basierend auf Task
        defaults = {
            "qa": {"temperature": 0.1, "max_tokens": 2048},
            "hyde": {"temperature": 0.3, "max_tokens": 512},
            "cot": {"temperature": 0.2, "max_tokens": 3072},
        }

        merged = {**defaults.get(task, defaults["qa"]), **task_cfg}
        return LLMTaskConfig(**merged)

    def get_index_names(self) -> tuple[str, str]:
        """Gibt (os_index, qdrant_collection) basierend auf Embedding-Config zurück."""
        emb = self.get_embedding_config()
        base_index = "chunks"

        if emb.index_suffix:
            return (
                f"{base_index}_{emb.index_suffix}",
                f"{base_index}_{emb.index_suffix}",
            )
        return base_index, base_index

    def get_chunking_config(self) -> ChunkingConfig:
        """Extrahiert Chunking-Konfiguration aus factors."""
        chunk_cfg = self.factors.get("chunking", {})
        return (
            ChunkingConfig(**chunk_cfg)
            if isinstance(chunk_cfg, dict)
            else ChunkingConfig()
        )

    def get_qrels_path(self) -> str:
        """
        Gibt den korrekten Qrels-Pfad basierend auf Chunking-Strategie zurück.

        Mapping:
        - by_title + 1800 → demo_qrels_1800.jsonl
        - semantic → demo_qrels_semantic.jsonl
        """
        chunking = self.get_chunking_config()
        suffix = chunking.get_qrels_suffix()
        return f"datasets/{self.dataset}_qrels_{suffix}.jsonl"

    def get_answers_path(self) -> str:
        """Gibt den Pfad zur Answers-Datei zurück."""
        return f"datasets/{self.dataset}_answers.jsonl"

    def get_queries_path(self) -> str:
        """Gibt den Pfad zur Queries-Datei zurück."""
        return f"datasets/{self.dataset}_queries.jsonl"
