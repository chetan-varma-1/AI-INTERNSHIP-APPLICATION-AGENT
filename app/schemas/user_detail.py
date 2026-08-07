"""API schemas for parsed resumes and cover letters."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class DocumentType(StrEnum):
    """Supported uploaded document categories."""

    RESUME = "resume"
    COVER_LETTER = "cover_letter"


class EducationItem(BaseModel):
    """Education entry extracted from a resume."""

    institution: str = ""
    degree: str = ""
    field_of_study: str = ""
    start_date: str = ""
    end_date: str = ""
    details: str = ""


class ProjectItem(BaseModel):
    """Project entry extracted from a resume."""

    name: str = ""
    description: str = ""
    technologies: list[str] = Field(default_factory=list)
    url: str = ""


class ExperienceItem(BaseModel):
    """Employment entry extracted from a resume."""

    company: str = ""
    role: str = ""
    start_date: str = ""
    end_date: str = ""
    responsibilities: list[str] = Field(default_factory=list)


class CertificationItem(BaseModel):
    """Certification entry extracted from a resume."""

    name: str = ""
    issuer: str = ""
    date: str = ""
    credential_url: str = ""


class ResumeData(BaseModel):
    """Structured fields extracted from a resume."""

    education: list[EducationItem] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    profile_summary: str = ""
    certifications: list[CertificationItem] = Field(default_factory=list)


class CoverLetterData(BaseModel):
    """Structured fields extracted from a cover letter."""

    applicant_name: str = ""
    email: str = ""
    phone_number: str = ""
    address: str | None = None
    date: str = ""
    hiring_manager_name: str | None = None
    company_name: str = ""
    company_address: str | None = None
    job_title: str = ""
    salutation: str = ""
    opening_paragraph: str = ""
    body_paragraphs: list[str] = Field(default_factory=list)
    why_this_company: str = ""
    closing_paragraph: str = ""
    signature: str = ""


class ParsedResumeResponse(BaseModel):
    """Persisted resume and its extracted content."""

    id: uuid.UUID
    user_id: uuid.UUID
    type: DocumentType = DocumentType.RESUME
    file_name: str
    file_path: str
    extracted: ResumeData
    created_at: datetime
    updated_at: datetime


class ParsedCoverLetterResponse(BaseModel):
    """Persisted cover letter and its extracted content."""

    id: uuid.UUID
    user_id: uuid.UUID
    type: DocumentType = DocumentType.COVER_LETTER
    file_name: str
    file_path: str
    extracted: CoverLetterData
    created_at: datetime
    updated_at: datetime


class ProfileSummaryResponse(BaseModel):
    """User identity, preferences, and generated matching summary."""

    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    name: str
    email: str
    location_preference: str | None = None
    skills: list[str] = Field(default_factory=list)
    profile_summary: str
