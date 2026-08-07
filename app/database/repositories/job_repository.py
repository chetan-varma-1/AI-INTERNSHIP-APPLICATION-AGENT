"""Job persistence for scraped internship listings."""

from __future__ import annotations

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job


class JobRepository:
    """Data-access layer for scraped jobs."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[Job]:
        """Return all stored jobs ordered by newest first."""
        stmt = select(Job).order_by(Job.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def replace_all(self, raw_jobs: list[dict[str, Any]]) -> int:
        """Replace all jobs with a fresh scrape batch and return insert count."""
        await self._session.execute(delete(Job))
        jobs = [self._to_model(raw) for raw in raw_jobs]
        self._session.add_all(jobs)
        await self._session.flush()
        return len(jobs)

    @staticmethod
    def _to_model(raw: dict[str, Any]) -> Job:
        title = str(raw.get("title", "")).strip()
        skills = raw.get("skills_required") or []
        if not isinstance(skills, list):
            skills = []
        return Job(
            title=title,
            company=str(raw.get("company", "")).strip(),
            location=str(raw.get("location", "")).strip(),
            description=str(raw.get("description", "")).strip(),
            required_skills=[str(skill).strip() for skill in skills if str(skill).strip()],
            salary=str(raw.get("stipend", "")).strip(),
            job_type=str(raw.get("job_type", "internship")).strip() or "internship",
            role=title,
            source=str(raw.get("source", "mock")).strip() or "mock",
            duration=str(raw.get("duration", "")).strip(),
            apply_url=str(raw.get("apply_url", "")).strip(),
        )
