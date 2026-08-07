"""Retrieval-augmented generation domain exceptions."""


class RAGError(Exception):
    """Base retrieval-augmented generation error."""


class InvalidVectorStoreConfigError(RAGError, ValueError):
    """Raised when vector store configuration cannot be interpreted."""


class VectorStoreConnectionError(RAGError, RuntimeError):
    """Raised when the configured Chroma server is unreachable."""
