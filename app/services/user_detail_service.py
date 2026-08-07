"""Business logic for uploaded resumes and cover letters."""

from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import UUID

from app.agents.cover_letter_agent import CoverLetterAgent
from app.agents.resume_agent import ResumeAgent
from app.database.repositories.user_detail_repository import UserDetailRepository
from app.models.user_detail import UserDetail
from app.schemas.user_detail import (
    CoverLetterData,
    DocumentType,
    ParsedCoverLetterResponse,
    ParsedResumeResponse,
    ResumeData,
)
from app.utils.file_utils import DocumentFileService


class UserDetailService:
    """Parse, persist, and list a user's uploaded documents."""

    def __init__(
        self,
        repository: UserDetailRepository,
        file_service: DocumentFileService,
        resume_agent: ResumeAgent,
        cover_letter_agent: CoverLetterAgent,
    ) -> None:
        self._repository = repository
        self._files = file_service
        self._resume_agent = resume_agent
        self._cover_letter_agent = cover_letter_agent

    async def parse_resume(
        self,
        user_id: UUID,
        file_name: str,
        content: bytes,
    ) -> ParsedResumeResponse:
        """Parse and persist a resume upload."""
        stored = await asyncio.to_thread(
            self._files.process,
            user_id,
            file_name,
            content,
        )
        try:
            extracted = await self._resume_agent.parse(stored.text)
            detail = await self._repository.create_resume(
                user_id=user_id,
                file_name=stored.original_name,
                file_path=str(stored.path),
                data=extracted,
            )
        except Exception:
            await asyncio.to_thread(self._remove_file, stored.path)
            raise
        return self._resume_response(detail, extracted)

    async def parse_cover_letter(
        self,
        user_id: UUID,
        file_name: str,
        content: bytes,
    ) -> ParsedCoverLetterResponse:
        """Parse and persist a cover-letter upload."""
        stored = await asyncio.to_thread(
            self._files.process,
            user_id,
            file_name,
            content,
        )
        try:
            extracted = await self._cover_letter_agent.parse(stored.text)
            detail = await self._repository.create_cover_letter(
                user_id=user_id,
                file_name=stored.original_name,
                file_path=str(stored.path),
                data=extracted,
            )
        except Exception:
            await asyncio.to_thread(self._remove_file, stored.path)
            raise
        return self._cover_letter_response(detail, extracted)

    async def list_resumes(self, user_id: UUID) -> list[ParsedResumeResponse]:
        """List parsed resumes for a user."""
        details = await self._repository.list_by_user(user_id, DocumentType.RESUME)
        return [self._resume_response(detail, self._resume_data(detail)) for detail in details]

    async def list_cover_letters(
        self,
        user_id: UUID,
    ) -> list[ParsedCoverLetterResponse]:
        """List parsed cover letters for a user."""
        details = await self._repository.list_by_user(
            user_id,
            DocumentType.COVER_LETTER,
        )
        return [
            self._cover_letter_response(detail, self._cover_letter_data(detail))
            for detail in details
        ]

    @staticmethod
    def _resume_data(detail: UserDetail) -> ResumeData:
        return ResumeData(
            education=detail.education,
            skills=detail.skills,
            projects=detail.projects,
            experience=detail.experience,
            profile_summary=detail.profile_summary or "",
            certifications=detail.certifications,
        )

    @staticmethod
    def _cover_letter_data(detail: UserDetail) -> CoverLetterData:
        return CoverLetterData(
            applicant_name=detail.applicant_name or "",
            email=detail.email or "",
            phone_number=detail.phone_number or "",
            address=detail.address,
            date=detail.letter_date or "",
            hiring_manager_name=detail.hiring_manager_name,
            company_name=detail.company_name or "",
            company_address=detail.company_address,
            job_title=detail.job_title or "",
            salutation=detail.salutation or "",
            opening_paragraph=detail.opening_paragraph or "",
            body_paragraphs=detail.body_paragraphs,
            why_this_company=detail.why_this_company or "",
            closing_paragraph=detail.closing_paragraph or "",
            signature=detail.signature or "",
        )

    @staticmethod
    def _resume_response(
        detail: UserDetail,
        extracted: ResumeData,
    ) -> ParsedResumeResponse:
        return ParsedResumeResponse(
            id=detail.id,
            user_id=detail.user_id,
            file_name=detail.file_name,
            file_path=detail.file_path,
            extracted=extracted,
            created_at=detail.created_at,
            updated_at=detail.updated_at,
        )

    @staticmethod
    def _cover_letter_response(
        detail: UserDetail,
        extracted: CoverLetterData,
    ) -> ParsedCoverLetterResponse:
        return ParsedCoverLetterResponse(
            id=detail.id,
            user_id=detail.user_id,
            file_name=detail.file_name,
            file_path=detail.file_path,
            extracted=extracted,
            created_at=detail.created_at,
            updated_at=detail.updated_at,
        )

    @staticmethod
    def _remove_file(path: Path) -> None:
        path.unlink(missing_ok=True)
