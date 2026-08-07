"""Semantic search over indexed internships."""

from __future__ import annotations

from typing import Any

from app.rag.config import RAGConfig
from app.rag.embeddings import EmbeddingService, OllamaEmbeddingService
from app.rag.vector_store import ChromaVectorStore, VectorStore
from app.schemas.rag import InternshipJob, SearchResult


class InternshipRetriever:
    """Retrieve internship listings matching a semantic query."""

    def __init__(
        self,
        config: RAGConfig | None = None,
        embedding_service: EmbeddingService | None = None,
        vector_store: VectorStore | None = None,
    ) -> None:
        self._config = config or RAGConfig()
        self._embeddings = embedding_service or OllamaEmbeddingService(self._config)
        self._store = vector_store or ChromaVectorStore(self._config)

    def search(
        self,
        query: str,
        top_k: int | None = None,
        filters: dict[str, str] | None = None,
    ) -> list[SearchResult]:
        """Return internships semantically similar to a query."""
        result_limit = top_k or self._config.default_top_k
        query_vector = self._embeddings.embed_query(query)
        raw_results = self._store.similarity_search(
            query_vector,
            result_limit,
            where=filters,
        )
        return self._parse_results(raw_results)

    def search_by_skills(
        self,
        skills: list[str],
        top_k: int | None = None,
    ) -> list[SearchResult]:
        """Search for internships mentioning the supplied skills."""
        query = f"Internship requiring skills: {', '.join(skills)}"
        return self.search(query, top_k=top_k)

    def search_by_location(
        self,
        location: str,
        top_k: int | None = None,
    ) -> list[SearchResult]:
        """Search for internships in a location."""
        return self.search(f"Internship in {location}", top_k=top_k)

    def _parse_results(self, raw_results: dict[str, Any]) -> list[SearchResult]:
        identifiers = raw_results.get("ids", [[]])[0]
        documents = raw_results.get("documents", [[]])[0]
        metadatas = raw_results.get("metadatas", [[]])[0]
        distances = raw_results.get("distances", [[]])[0]

        results: list[SearchResult] = []
        for job_id, document, raw_metadata, distance in zip(
            identifiers,
            documents,
            metadatas,
            distances,
        ):
            metadata = {
                key: str(value)
                for key, value in (raw_metadata or {}).items()
            }
            results.append(
                SearchResult(
                    job_id=job_id,
                    score=1.0 - float(distance),
                    document=document or "",
                    metadata=metadata,
                    job=_metadata_to_job(metadata) if metadata else None,
                )
            )
        return results


def _metadata_to_job(metadata: dict[str, str]) -> InternshipJob:
    skills = [
        skill.strip()
        for skill in metadata.get("skills", "").split(",")
        if skill.strip()
    ]
    return InternshipJob(
        title=metadata.get("title", ""),
        company=metadata.get("company", ""),
        description=metadata.get("description", ""),
        skills_required=skills,
        location=metadata.get("location", ""),
        apply_url=metadata.get("apply_url", ""),
        source=metadata.get("source", "mock"),
        job_type=metadata.get("job_type", "internship"),
        stipend=metadata.get("stipend", ""),
        duration=metadata.get("duration", ""),
    )
