"""Ollama-backend embedding service"""
from __future__ import annotations
from abc import ABC, abstractmethod

from langchain_ollama import OllamaEmbeddings

from rag.config import RAGConfig

class EmbeddingService(ABC):
    """Embedding provier contract (dependency inversion)"""
    @abstractmethod
    def embed_documents(self, text: list[str]) -> list[list[float]]:
        """Embed multiple documents."""
    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Embed a singl search query.""" 



