"""RAG configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from app.rag.exceptions import InvalidVectorStoreConfigError

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ChromaMode = Literal["embedded", "http"]

EMBEDDED_MODE: ChromaMode = "embedded"
HTTP_MODE: ChromaMode = "http"
SUPPORTED_CHROMA_MODES: frozenset[str] = frozenset({EMBEDDED_MODE, HTTP_MODE})

DEFAULT_CHROMA_MODE: ChromaMode = HTTP_MODE
DEFAULT_CHROMA_HOST = "localhost"
DEFAULT_CHROMA_PORT = 6333

CHROMA_MODE_ENV_VAR = "CHROMA_MODE"
CHROMA_HOST_ENV_VAR = "CHROMA_HOST"
CHROMA_PORT_ENV_VAR = "CHROMA_PORT"


def _resolve_chroma_mode() -> ChromaMode:
    """Read the client mode from the environment, defaulting to server mode."""
    mode = os.getenv(CHROMA_MODE_ENV_VAR, DEFAULT_CHROMA_MODE).strip().lower()
    if mode not in SUPPORTED_CHROMA_MODES:
        raise InvalidVectorStoreConfigError(
            f"{CHROMA_MODE_ENV_VAR} must be one of {sorted(SUPPORTED_CHROMA_MODES)}, got {mode!r}"
        )
    return mode  # type: ignore[return-value]


def _resolve_chroma_port() -> int:
    """Read the server port from the environment."""
    raw_port = os.getenv(CHROMA_PORT_ENV_VAR, str(DEFAULT_CHROMA_PORT)).strip()
    try:
        return int(raw_port)
    except ValueError as error:
        raise InvalidVectorStoreConfigError(
            f"{CHROMA_PORT_ENV_VAR} must be an integer, got {raw_port!r}"
        ) from error


@dataclass(frozen=True)
class RAGConfig:
    """Central configuration for embedding, storage, and retrieval."""

    embedding_model: str = "mxbai-embed-large"
    ollama_base_url: str = "http://localhost:11434"
    collection_name: str = "internships"
    persist_dir: Path = PROJECT_ROOT / "vector_db"
    default_top_k: int = 5

    chroma_mode: ChromaMode = field(default_factory=_resolve_chroma_mode)
    chroma_host: str = field(
        default_factory=lambda: os.getenv(CHROMA_HOST_ENV_VAR, DEFAULT_CHROMA_HOST)
    )
    chroma_port: int = field(default_factory=_resolve_chroma_port)

    @property
    def chroma_url(self) -> str:
        """Return the HTTP endpoint of the configured Chroma server."""
        return f"http://{self.chroma_host}:{self.chroma_port}"
