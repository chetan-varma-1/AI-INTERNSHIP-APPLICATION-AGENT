"""Unit tests for RAG configuration (no Chroma server required)."""

from __future__ import annotations

import pytest

from app.rag.config import (
    CHROMA_HOST_ENV_VAR,
    CHROMA_MODE_ENV_VAR,
    CHROMA_PORT_ENV_VAR,
    DEFAULT_CHROMA_HOST,
    DEFAULT_CHROMA_PORT,
    EMBEDDED_MODE,
    HTTP_MODE,
    RAGConfig,
)
from app.rag.exceptions import InvalidVectorStoreConfigError


class TestRAGConfig:
    """Environment-driven Chroma client configuration."""

    def test_defaults_to_http_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv(CHROMA_MODE_ENV_VAR, raising=False)
        monkeypatch.delenv(CHROMA_HOST_ENV_VAR, raising=False)
        monkeypatch.delenv(CHROMA_PORT_ENV_VAR, raising=False)

        config = RAGConfig()

        assert config.chroma_mode == HTTP_MODE
        assert config.chroma_host == DEFAULT_CHROMA_HOST
        assert config.chroma_port == DEFAULT_CHROMA_PORT

    def test_embedded_mode_from_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(CHROMA_MODE_ENV_VAR, "EMBEDDED")

        assert RAGConfig().chroma_mode == EMBEDDED_MODE

    def test_host_and_port_overrides(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(CHROMA_HOST_ENV_VAR, "chroma.internal")
        monkeypatch.setenv(CHROMA_PORT_ENV_VAR, "8000")

        config = RAGConfig()

        assert config.chroma_url == "http://chroma.internal:8000"

    def test_unknown_mode_fails_fast(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(CHROMA_MODE_ENV_VAR, "sqlite")

        with pytest.raises(InvalidVectorStoreConfigError):
            RAGConfig()

    def test_non_numeric_port_fails_fast(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(CHROMA_PORT_ENV_VAR, "not-a-port")

        with pytest.raises(InvalidVectorStoreConfigError):
            RAGConfig()
