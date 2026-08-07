"""Scrape mock jobs and persist them to Postgres + RAG in parallel."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from app.database.connection import SessionLocal
from app.database.repositories.job_repository import JobRepository
from app.rag.ingestion import IngestionPipeline
from app.schemas.job import ScrapeJobsResponse
from app.scraper.mocker_scraper import MockScraper

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StaticJobSource:
    """Job source that returns a pre-scraped batch."""

    jobs: list[dict[str, Any]]

    def scraper(self) -> list[dict[str, Any]]:
        """Return the captured scrape payload."""
        return self.jobs


class JobScrapeService:
    """Run the mock scraper, then persist to DB and vector store in parallel."""

    def __init__(self, job_source: MockScraper | None = None) -> None:
        self._job_source = job_source or MockScraper()

    async def run(self, *, reset_vectors: bool = True) -> ScrapeJobsResponse:
        """Scrape once, then persist to Postgres and RAG concurrently."""
        raw_jobs = await asyncio.to_thread(self._job_source.scraper)
        scraped_count = len(raw_jobs)
        if scraped_count == 0:
            return ScrapeJobsResponse(
                scraped_count=0,
                db_inserted_count=0,
                rag_indexed_count=0,
                message="No jobs returned by scraper",
            )

        # The async engine pool is bound to the running loop, so database work stays
        # on it while the blocking Chroma ingestion runs in a worker thread.
        db_inserted_count, rag_indexed_count = await asyncio.gather(
            self._persist_jobs(raw_jobs),
            asyncio.to_thread(self._ingest_rag_sync, raw_jobs, reset_vectors),
        )

        return ScrapeJobsResponse(
            scraped_count=scraped_count,
            db_inserted_count=db_inserted_count,
            rag_indexed_count=rag_indexed_count,
            message=(
                "Scrape complete: jobs saved to Postgres and indexed in RAG in parallel"
            ),
        )

    @staticmethod
    async def _persist_jobs(raw_jobs: list[dict[str, Any]]) -> int:
        """Replace the jobs table with the scrape batch and return the row count."""
        async with SessionLocal() as session:
            try:
                count = await JobRepository(session).replace_all(raw_jobs)
                await session.commit()
                logger.info("Inserted %s jobs into PostgreSQL", count)
                return count
            except Exception:
                await session.rollback()
                raise

    @staticmethod
    def _ingest_rag_sync(raw_jobs: list[dict[str, Any]], reset_vectors: bool) -> int:
        """Index the same scrape batch into ChromaDB from a worker thread."""
        count = IngestionPipeline(job_source=StaticJobSource(raw_jobs)).run(reset=reset_vectors)
        logger.info("Indexed %s jobs into RAG", count)
        return count
