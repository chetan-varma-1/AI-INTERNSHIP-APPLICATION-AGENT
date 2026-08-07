"""Pydantic schemas package."""

from app.schemas.auth import (
    AuthMessageResponse,
    LoginRequest,
    MessageResponse,
    SignupRequest,
    UserPublic,
)
from app.schemas.job import JobPublic, ScrapeJobsResponse
from app.schemas.rag import InternshipJob, SearchResult

__all__ = [
    "AuthMessageResponse",
    "InternshipJob",
    "JobPublic",
    "LoginRequest",
    "MessageResponse",
    "ScrapeJobsResponse",
    "SearchResult",
    "SignupRequest",
    "UserPublic",
]
