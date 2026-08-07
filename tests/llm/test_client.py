"""Tests for Ollama structured extraction."""

import pytest
from pydantic import BaseModel

from app.core.exceptions import DocumentParsingError
from app.llm.client import OllamaStructuredExtractionClient
from app.schemas.user_detail import ResumeData


class FakeStructuredModel:
    """Deterministic structured-model runnable."""

    def __init__(self, result: object = None, error: Exception | None = None) -> None:
        self._result = result
        self._error = error

    async def ainvoke(self, _prompt: str) -> object:
        """Return the configured result or raise the configured error."""
        if self._error is not None:
            raise self._error
        return self._result


class FakeChatModel:
    """Capture structured-output configuration without calling Ollama."""

    def __init__(self, runnable: FakeStructuredModel) -> None:
        self._runnable = runnable
        self.method: str | None = None

    def with_structured_output(
        self,
        _schema: type[BaseModel],
        *,
        method: str,
    ) -> FakeStructuredModel:
        """Record the requested extraction method."""
        self.method = method
        return self._runnable


class TestOllamaStructuredExtractionClient:
    """Structured response and actionable failure behavior."""

    @staticmethod
    def _client(runnable: FakeStructuredModel) -> tuple[
        OllamaStructuredExtractionClient,
        FakeChatModel,
    ]:
        client = OllamaStructuredExtractionClient(
            model="llama3.2:1b",
            base_url="http://localhost:11434",
        )
        fake_model = FakeChatModel(runnable)
        client._model = fake_model  # type: ignore[assignment]
        return client, fake_model

    @pytest.mark.asyncio
    async def test_extracts_schema_with_json_mode(self) -> None:
        client, fake_model = self._client(FakeStructuredModel({"skills": ["Python"]}))

        result = await client.extract("Python developer", ResumeData, "Extract resume")

        assert result.skills == ["Python"]
        assert fake_model.method == "json_schema"

    @pytest.mark.asyncio
    async def test_reports_missing_model_action(self) -> None:
        client, _ = self._client(
            FakeStructuredModel(error=RuntimeError("model 'llama3.2:1b' not found"))
        )

        with pytest.raises(DocumentParsingError, match="ollama pull llama3.2:1b"):
            await client.extract("Resume", ResumeData, "Extract resume")
