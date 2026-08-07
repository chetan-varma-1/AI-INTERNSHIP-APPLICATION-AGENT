"""Ingest internship listings into the vector store."""

from __future__ import annotations

import logging
from typing import Protocol

from app.rag.config import RAGConfig
from app.rag.embeddings import EmbeddingService, OllamaEmbeddingService
from app.rag.vector_store import ChromaVectorStore, VectorStore
from app.schemas.rag import InternshipJob
from app.scraper.mocker_scraper import MockScraper

logger = logging.getLogger(__name__)

BATCH_SIZE = 32


class JobSource(Protocol):
    """Contract for a source of raw internship records."""

    def scraper(self) -> list[dict]:
        """Return raw internship records."""


class IngestionPipeline:
    """Load jobs, create embeddings, and persist them."""

    def __init__(
        self,
        config: RAGConfig | None = None,
        job_source: JobSource | None = None,
        embedding_service: EmbeddingService | None = None,
        vector_store: VectorStore | None = None,
    ) -> None:
        self._config = config or RAGConfig()
        self._job_source = job_source or MockScraper()
        self._embeddings = embedding_service or OllamaEmbeddingService(self._config)
        self._store = vector_store or ChromaVectorStore(self._config)

    def run(self, *, reset: bool = False) -> int:
        """Ingest all available jobs and return the number indexed."""
        jobs = self._load_jobs()
        if not jobs:
            logger.warning("No internship jobs found to ingest")
            return 0

        if reset:
            self._store.reset()

        indexed_count = 0
        for batch in _chunk(jobs, BATCH_SIZE):
            self._store.upsert(
                ids=[job.document_id for job in batch],
                embeddings=self._embeddings.embed_documents(
                    [job.to_document_text() for job in batch]
                ),
                documents=[job.to_document_text() for job in batch],
                metadatas=[job.to_metadata() for job in batch],
            )
            indexed_count += len(batch)
            logger.info("Indexed %s of %s internships", indexed_count, len(jobs))

        return indexed_count

    def _load_jobs(self) -> list[InternshipJob]:
        seen_ids: set[str] = set()
        unique_jobs: list[InternshipJob] = []

        for raw_job in self._job_source.scraper():
            job = InternshipJob.model_validate(raw_job)
            if job.document_id in seen_ids:
                continue
            seen_ids.add(job.document_id)
            unique_jobs.append(job)

        return unique_jobs


def _chunk(items: list[InternshipJob], size: int) -> list[list[InternshipJob]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def ingest_internships(*, reset: bool = False) -> int:
    """Run the default internship ingestion pipeline."""
    logging.basicConfig(level=logging.INFO)
    return IngestionPipeline().run(reset=reset)


if __name__ == "__main__":
    logger.info("Ingested %s internships into ChromaDB", ingest_internships(reset=True))
