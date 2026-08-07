"""Dependency providers for document and matching workflows."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.cover_letter_agent import CoverLetterAgent
from app.agents.job_retrieval_agent import JobRetrievalAgent
from app.agents.orchestrator import MatchingOrchestrator
from app.agents.resume_agent import ResumeAgent
from app.core.config import Settings, get_settings
from app.database.connection import get_db
from app.database.repositories.user_detail_repository import UserDetailRepository
from app.database.repositories.user_repository import UserRepository
from app.llm.client import OllamaStructuredExtractionClient
from app.rag.retriever import InternshipRetriever
from app.services.job_scrape_service import JobScrapeService
from app.services.profile_service import ProfileService
from app.services.user_detail_service import UserDetailService
from app.utils.file_utils import DocumentFileService


def get_user_detail_service(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> UserDetailService:
    """Provide the parsed-document service."""
    extraction_client = OllamaStructuredExtractionClient(
        model=settings.ollama_chat_model,
        base_url=settings.ollama_base_url,
    )
    return UserDetailService(
        repository=UserDetailRepository(db),
        file_service=DocumentFileService(
            settings.upload_dir,
            settings.max_upload_size_mb,
        ),
        resume_agent=ResumeAgent(extraction_client),
        cover_letter_agent=CoverLetterAgent(extraction_client),
    )


def get_profile_service(db: AsyncSession = Depends(get_db)) -> ProfileService:
    """Provide the user profile summary service."""
    return ProfileService(UserRepository(db))


def get_matching_orchestrator(
    db: AsyncSession = Depends(get_db),
) -> MatchingOrchestrator:
    """Provide the multi-agent matching orchestrator."""
    return MatchingOrchestrator(
        user_repository=UserRepository(db),
        detail_repository=UserDetailRepository(db),
        retrieval_agent=JobRetrievalAgent(InternshipRetriever()),
    )


def get_job_scrape_service() -> JobScrapeService:
    """Provide the mock scrape + parallel persist service."""
    return JobScrapeService()
