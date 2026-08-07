"""ChromaDB vector store wrapper."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import chromadb
from chromadb.api.client import ClientAPI
from chromadb.api.models.Collection import Collection

from app.rag.config import HTTP_MODE, RAGConfig
from app.rag.exceptions import VectorStoreConnectionError


class VectorStore(ABC):
    """Vector persistence contract."""

    @abstractmethod
    def upsert(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, str]],
    ) -> None:
        """Insert or update vectors."""

    @abstractmethod
    def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return nearest neighbors for an embedding."""

    @abstractmethod
    def count(self) -> int:
        """Return the stored document count."""

    @abstractmethod
    def reset(self) -> None:
        """Delete and recreate the collection."""


class ChromaVectorStore(VectorStore):
    """ChromaDB collection for internship embeddings.

    Backed either by a standalone Chroma server or by an on-disk embedded
    store, selected through :class:`RAGConfig`.
    """

    def __init__(self, config: RAGConfig | None = None) -> None:
        config = config or RAGConfig()
        self._collection_name = config.collection_name
        self._client = self._build_client(config)
        self._collection: Collection = self._create_collection()

    def upsert(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict[str, str]],
    ) -> None:
        """Insert or update vectors."""
        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return nearest neighbors for an embedding."""
        query: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            query["where"] = where
        return self._collection.query(**query)

    def count(self) -> int:
        """Return the stored document count."""
        return self._collection.count()

    def reset(self) -> None:
        """Delete and recreate the collection."""
        self._client.delete_collection(self._collection_name)
        self._collection = self._create_collection()

    def _create_collection(self) -> Collection:
        return self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    @staticmethod
    def _build_client(config: RAGConfig) -> ClientAPI:
        """Return a Chroma client for the configured mode.

        Raises:
            VectorStoreConnectionError: If the Chroma server is unreachable.
        """
        if config.chroma_mode != HTTP_MODE:
            config.persist_dir.mkdir(parents=True, exist_ok=True)
            return chromadb.PersistentClient(path=str(config.persist_dir))

        try:
            return chromadb.HttpClient(host=config.chroma_host, port=config.chroma_port)
        except Exception as error:
            raise VectorStoreConnectionError(
                f"Cannot reach the Chroma server at {config.chroma_url}. "
                "Start it with Docker or set CHROMA_MODE=embedded."
            ) from error
