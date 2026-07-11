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