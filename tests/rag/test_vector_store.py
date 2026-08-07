"""Unit tests for Chroma client selection (no Chroma server required)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.rag.config import EMBEDDED_MODE, HTTP_MODE, RAGConfig
from app.rag.exceptions import VectorStoreConnectionError
from app.rag.vector_store import ChromaVectorStore


@pytest.fixture
def http_config() -> RAGConfig:
    return RAGConfig(chroma_mode=HTTP_MODE, chroma_host="localhost", chroma_port=6333)


class TestChromaVectorStoreClientSelection:
    """The configured mode decides which Chroma client is built."""

    def test_http_mode_builds_http_client(self, http_config: RAGConfig) -> None:
        with patch("app.rag.vector_store.chromadb") as chroma:
            ChromaVectorStore(http_config)

        chroma.HttpClient.assert_called_once_with(host="localhost", port=6333)
        chroma.PersistentClient.assert_not_called()

    def test_embedded_mode_builds_persistent_client(self, tmp_path: Path) -> None:
        config = RAGConfig(
            chroma_mode=EMBEDDED_MODE, persist_dir=tmp_path / "vector_db"
        )

        with patch("app.rag.vector_store.chromadb") as chroma:
            ChromaVectorStore(config)

        chroma.PersistentClient.assert_called_once_with(path=str(config.persist_dir))
        chroma.HttpClient.assert_not_called()
        assert config.persist_dir.exists()

    def test_unreachable_server_raises_connection_error(
        self, http_config: RAGConfig
    ) -> None:
        with patch("app.rag.vector_store.chromadb") as chroma:
            chroma.HttpClient.side_effect = ConnectionError("refused")

            with pytest.raises(VectorStoreConnectionError, match="localhost:6333"):
                ChromaVectorStore(http_config)

    def test_collection_created_with_cosine_space(self, http_config: RAGConfig) -> None:
        client = MagicMock()

        with patch("app.rag.vector_store.chromadb") as chroma:
            chroma.HttpClient.return_value = client
            ChromaVectorStore(http_config)

        client.get_or_create_collection.assert_called_once_with(
            name=http_config.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
