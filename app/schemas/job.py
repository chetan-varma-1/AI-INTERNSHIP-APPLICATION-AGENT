"""API schemas for scraped internship jobs."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JobPublic(BaseModel):
    """Job record returned to clients."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    title: str
    company: str
    location: str
    description: str
    required_skills: list[str] = Field(default_factory=list)
    salary: str = ""
    type: str = Field(validation_alias="job_type", serialization_alias="type")
    role: str = ""
    source: str = "mock"
    duration: str = ""
    apply_url: str = ""
    created_at: datetime


class ScrapeJobsResponse(BaseModel):
    """Result of a scrape + parallel Postgres/RAG persist run."""

    scraped_count: int
    db_inserted_count: int
    rag_indexed_count: int
    message: str
