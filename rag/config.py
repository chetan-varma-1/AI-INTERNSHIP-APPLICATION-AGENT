"""RAG configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RAGConfig:
    """Central configuration for embedding, storage, and retrieval."""

    embedding_model: str = "mxbai-embed-large"
    ollama_base_url: str = "http://localhost:11434"
    collection_name: str = "internships"
    persist_dir: Path = Path(__file__).resolve().parent / "chroma_db"
    default_top_k: int = 5
