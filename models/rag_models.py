"""Pydantic models for the internship RAG pipeline."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from pydantic import BaseModel, Field, field_validator


class InternshipJob(BaseModel):
    """Structured internship record from the scraper."""

    title: str
    company: str
    description: str
    skills_required: list[str] = Field(default_factory=list)
    location: str
    apply_url: str
    source: str = "mock"
    job_type: str = "internship"
    stipend: str = ""
    duration: str = ""

    @field_validator("skills_required", mode="before")
    @classmethod
    def _normalize_skills(cls, value: Any) -> list[str]:
        if value is None:
            return []
        return [str(skill).strip() for skill in value if str(skill).strip()]

    @property
    def document_id(self) -> str:
        """Stable identifier for vector-store indexing."""
        payload = self.model_dump_json()
        slug = re.sub(r"[^a-z0-9]+", "_", f"{self.company}_{self.title}".lower()).strip("_")[:50]
        digest = hashlib.sha256(payload.encode()).hexdigest()[:12]
        return f"{slug}_{digest}"

    def to_document_text(self) -> str:
        """Flatten job fields into a single embedding-friendly string."""
        skills = ", ".join(self.skills_required)
        return (
            f"Title: {self.title}\n"
            f"Company: {self.company}\n"
            f"Location: {self.location}\n"
            f"Job Type: {self.job_type}\n"
            f"Stipend: {self.stipend}\n"
            f"Duration: {self.duration}\n"
            f"Skills: {skills}\n"
            f"Description: {self.description}"
        )

    def to_metadata(self) -> dict[str, str]:
        """Chroma-compatible flat metadata for filtering."""
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "description": self.description,
            "apply_url": self.apply_url,
            "source": self.source,
            "job_type": self.job_type,
            "stipend": self.stipend,
            "duration": self.duration,
            "skills": ", ".join(self.skills_required),
        }


class SearchResult(BaseModel):
    """Single retrieval hit from the vector store."""

    job_id: str
    score: float
    document: str
    metadata: dict[str, str]
    job: InternshipJob | None = None
