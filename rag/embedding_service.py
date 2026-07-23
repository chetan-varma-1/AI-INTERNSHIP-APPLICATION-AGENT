"""Ollama-backed embedding service."""

from __future__ import annotations

from abc import ABC, abstractmethod

from langchain_ollama import OllamaEmbeddings

from rag.config import RAGConfig


class EmbeddingService(ABC):
    """Embedding provider contract (dependency inversion)."""

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple documents."""

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Embed a single search query."""


class OllamaEmbeddingService(EmbeddingService):
    """Embeds text via Ollama using mxbai-embed-large (or configured model)."""

    def __init__(self, config: RAGConfig | None = None) -> None:
        cfg = config or RAGConfig()
        self._model = OllamaEmbeddings(
            model=cfg.embedding_model,
            base_url=cfg.ollama_base_url,
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return self._model.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._model.embed_query(text)
