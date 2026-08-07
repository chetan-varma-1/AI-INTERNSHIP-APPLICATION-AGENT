"""Jobs HTTP routes: scrape runner and job listing."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_job_scrape_service
from app.auth.dependencies import get_current_user
from app.database.connection import get_db
from app.database.repositories.job_repository import JobRepository
from app.rag.exceptions import RAGError
from app.schemas.job import JobPublic, ScrapeJobsResponse
from app.services.job_scrape_service import JobScrapeService

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/scrape", response_model=ScrapeJobsResponse)
async def run_scraper(
    reset_vectors: bool = Query(
        default=True,
        description="Reset the Chroma collection before RAG ingestion",
    ),
    service: JobScrapeService = Depends(get_job_scrape_service),
) -> ScrapeJobsResponse:
    """Run the mock scraper, then save to Postgres and RAG in parallel threads."""
    try:
        return await service.run(reset_vectors=reset_vectors)
    except RAGError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"RAG ingestion failed: {exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scrape pipeline failed: {exc}",
        ) from exc


@router.get("", response_model=list[JobPublic])
async def list_jobs(db: AsyncSession = Depends(get_db)) -> list[JobPublic]:
    """List scraped jobs stored in PostgreSQL."""
    jobs = await JobRepository(db).list_all()
    return [JobPublic.model_validate(job) for job in jobs]
