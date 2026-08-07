"""Persistence operations for parsed user documents."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_detail import UserDetail
from app.schemas.user_detail import CoverLetterData, DocumentType, ResumeData


class UserDetailRepository:
    """Data-access layer for resumes and cover letters."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_resume(
        self,
        *,
        user_id: UUID,
        file_name: str,
        file_path: str,
        data: ResumeData,
    ) -> UserDetail:
        """Persist an extracted resume."""
        detail = UserDetail(
            user_id=user_id,
            document_type=DocumentType.RESUME.value,
            file_name=file_name,
            file_path=file_path,
            education=[item.model_dump() for item in data.education],
            skills=data.skills,
            projects=[item.model_dump() for item in data.projects],
            experience=[item.model_dump() for item in data.experience],
            profile_summary=data.profile_summary,
            certifications=[item.model_dump() for item in data.certifications],
        )
        return await self._add(detail)

    async def create_cover_letter(
        self,
        *,
        user_id: UUID,
        file_name: str,
        file_path: str,
        data: CoverLetterData,
    ) -> UserDetail:
        """Persist an extracted cover letter."""
        detail = UserDetail(
            user_id=user_id,
            document_type=DocumentType.COVER_LETTER.value,
            file_name=file_name,
            file_path=file_path,
            applicant_name=data.applicant_name,
            email=data.email,
            phone_number=data.phone_number,
            address=data.address,
            letter_date=data.date,
            hiring_manager_name=data.hiring_manager_name,
            company_name=data.company_name,
            company_address=data.company_address,
            job_title=data.job_title,
            salutation=data.salutation,
            opening_paragraph=data.opening_paragraph,
            body_paragraphs=data.body_paragraphs,
            why_this_company=data.why_this_company,
            closing_paragraph=data.closing_paragraph,
            signature=data.signature,
        )
        return await self._add(detail)

    async def get_by_id(self, detail_id: UUID) -> UserDetail | None:
        """Fetch a document by primary key."""
        result = await self._session.execute(select(UserDetail).where(UserDetail.id == detail_id))
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: UUID,
        document_type: DocumentType,
    ) -> list[UserDetail]:
        """List a user's documents of one type, newest first."""
        result = await self._session.execute(
            select(UserDetail)
            .where(
                UserDetail.user_id == user_id,
                UserDetail.document_type == document_type.value,
            )
            .order_by(UserDetail.created_at.desc())
        )
        return list(result.scalars().all())

    async def _add(self, detail: UserDetail) -> UserDetail:
        self._session.add(detail)
        await self._session.flush()
        await self._session.refresh(detail)
        return detail
