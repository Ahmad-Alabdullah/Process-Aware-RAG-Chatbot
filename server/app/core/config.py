import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # === Datenbanken & Backends ===
    DATABASE_URL: str
    REDIS_URL: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    PGADMIN_EMAIL: str
    PGADMIN_PASSWORD: str

    OPENSEARCH_URL: str
    OS_INDEX: str = "chunks"

    QDRANT_URL: str
    QDRANT_COLLECTION: str = "chunks"

    OS_QWEN3_INDEX: str
    QDRANT_QWEN3_COLLECTION: str

    OS_SEMANTIC_INDEX: str
    QDRANT_SEMANTIC_COLLECTION: str

    # Sentence-level semantic chunking (LangChain)
    OS_SEMANTIC_SENTENCE_QWEN3_INDEX: str = "chunks_semantic_sentence_qwen3"
    QDRANT_SEMANTIC_SENTENCE_QWEN3_COLLECTION: str = "chunks_semantic_sentence_qwen3"

    # === Embeddings & Modelle ===
    EMBEDDING_BACKEND: str = "hf"  # options: 'ollama', 'hf'
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    OLLAMA_BASE: str = "http://ollama:11434"
    OLLAMA_EMBED_MODEL: str = "qwen3-embedding:4b"
    OLLAMA_MODEL: str

    # === Retrieval ===
    TOP_K: int
    RRF_K: int

    # === Graph (Neo4j) ===
    NEO4J_URL: str
    NEO4J_PASSWORD: str
    NEO4J_USER: str = "neo4j"

    # === QA & Framework ===
    QA_FRAMEWORK: str = "LC"  # LC or LI
    HYDE: bool = False

    # === Local or docker ===
    ENV: str

    # === Dokumentenverarbeitung ===
    MAX_CHARACTERS: int
    NEW_AFTER_N_CHARS: int
    OVERLAP: int
    OCR_LANGUAGES: str
    MAX_SEMANTIC_CHARACTERS: int

    # === Pydantic Settings Config ===
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._apply_env_overrides()

    def _apply_env_overrides(self):
        """Passe URLs automatisch an je nach Umgebung (Docker vs. lokal)."""
        if self.ENV == "local":
            self.REDIS_URL = "redis://localhost:6379/0"
            self.DATABASE_URL = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@localhost:5432/proto"
            self.OPENSEARCH_URL = "http://localhost:9200"
            self.QDRANT_URL = "http://localhost:6333"
            self.NEO4J_URL = "bolt://localhost:7687"
            self.OLLAMA_BASE = "http://localhost:11434"
        else:
            self.REDIS_URL = self.REDIS_URL or "redis://redis:6379"
            self.DATABASE_URL = (
                self.DATABASE_URL
                or f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@postgres:5432/proto"
            )
            self.OPENSEARCH_URL = self.OPENSEARCH_URL or "http://opensearch:9200"
            self.QDRANT_URL = self.QDRANT_URL or "http://qdrant:6333"
            self.NEO4J_URL = self.NEO4J_URL or "bolt://neo4j:7687"
            self.OLLAMA_BASE = self.OLLAMA_BASE or "http://ollama:11434"


settings = Settings()  # type: ignore
