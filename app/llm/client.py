"""Structured LLM extraction contracts and Ollama implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from langchain_ollama import ChatOllama
from pydantic import BaseModel

from app.core.exceptions import DocumentParsingError

StructuredModel = TypeVar("StructuredModel", bound=BaseModel)
MAX_DOCUMENT_CHARACTERS = 60_000


class StructuredExtractionClient(ABC):
    """Contract for extracting a Pydantic model from unstructured text."""

    @abstractmethod
    async def extract(
        self,
        text: str,
        schema: type[StructuredModel],
        instructions: str,
    ) -> StructuredModel:
        """Extract and validate structured data."""


class OllamaStructuredExtractionClient(StructuredExtractionClient):
    """Use an Ollama chat model for schema-constrained extraction."""

    def __init__(self, *, model: str, base_url: str) -> None:
        self._model_name = model
        self._model = ChatOllama(model=model, base_url=base_url, temperature=0)

    async def extract(
        self,
        text: str,
        schema: type[StructuredModel],
        instructions: str,
    ) -> StructuredModel:
        """Extract a validated model from document text."""
        prompt = (
            f"{instructions}\n"
            "Use only facts present in the document. Use empty strings or lists "
            "when a field is absent; never invent information. Return exactly one "
            "JSON object matching the supplied response schema.\n\n"
            f"DOCUMENT:\n{text[:MAX_DOCUMENT_CHARACTERS]}"
        )
        try:
            structured_model = self._model.with_structured_output(
                schema,
                method="json_schema",
            )
            result = await structured_model.ainvoke(prompt)
            return result if isinstance(result, schema) else schema.model_validate(result)
        except Exception as exc:
            raise DocumentParsingError(self._error_message(exc)) from exc

    def _error_message(self, error: Exception) -> str:
        error_text = str(error).casefold()
        if "model" in error_text and "not found" in error_text:
            return (
                f"Ollama model '{self._model_name}' is not installed. "
                f"Run: ollama pull {self._model_name}"
            )
        if "connection" in error_text or "connect" in error_text:
            return "Ollama is unavailable. Start Ollama and retry the request"
        return (
            f"Ollama model '{self._model_name}' could not produce the required "
            "structured document response"
        )
