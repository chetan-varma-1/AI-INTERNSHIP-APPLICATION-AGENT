"""ChromaDB vector store wrapper"""

from __future__ import annotations
from typing import Any
from abc import ABC, abstractmethod
import chromadb
from chromadb.api.models.Collection import Collection

from rag.config import RAGConfig

class VectorStore(ABC):
    """Vector persistence contract"""

    @abstractmethod
    def upsert(
        self,
        ids: list [str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, str]],
    ) -> None:
        """insert or update vectors."""

    @abstractmethod
    def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]: 
        """Return nearest neighbors for a query embedding"""
    
    @abstractmethod
    def count(self) -> int:
        """Return stored document count."""
    
    @abstractmethod
    def reset(self) -> None:
        """Delete and recreate the collections."""

class ChromaVectorStore(VectorStore):
    """Persistent ChromaDB collection for internship embeddings"""
    def __init__(self, config: RAGConfig | None = None) -> None:
        cfg = config  or RAGConfig()
        self._collection_name = cfg.collection_name
        cfg.persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(cfg.persist_dir))
        self._collection: Collection = self._create_collection()

    


