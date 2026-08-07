"""Orchestrator for profile resolution and internship retrieval."""

from __future__ import annotations

from uuid import UUID

from app.agents.job_retrieval_agent import JobRetrievalAgent
from app.core.exceptions import (
    InvalidDocumentSelectionError,
    ResourceAccessDeniedError,
    ResourceNotFoundError,
)
from app.database.repositories.user_detail_repository import UserDetailRepository
from app.database.repositories.user_repository import UserRepository
from app.models.user_detail import UserDetail
from app.schemas.matching import MatchingProfile, MatchingRequest, MatchingResponse
from app.schemas.user_detail import DocumentType

DEFAULT_MATCH_COUNT = 5


class MatchingOrchestrator:
    """Resolve candidate data and coordinate semantic job retrieval."""

    def __init__(
        self,
        user_repository: UserRepository,
        detail_repository: UserDetailRepository,
        retrieval_agent: JobRetrievalAgent,
    ) -> None:
        self._users = user_repository
        self._details = detail_repository
        self._retrieval_agent = retrieval_agent

    async def match(self, user_id: UUID, request: MatchingRequest) -> MatchingResponse:
        """Build a candidate profile and return ranked internship matches."""
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise ResourceNotFoundError("User not found")

        detail = await self._resolve_detail(user_id, request)
        profile_skills = user.profile.skills if user.profile else []
        resume_skills = detail.skills if detail is not None else []
        profile = MatchingProfile(
            user_id=user.id,
            name=user.name,
            email=user.email,
            location_preference=(user.profile.location_preference if user.profile else None),
            education=detail.education if detail is not None else [],
            skills=self._merge_skills(profile_skills, resume_skills),
            projects=detail.projects if detail is not None else [],
            experience=detail.experience if detail is not None else [],
            profile_summary=(detail.profile_summary or "") if detail is not None else "",
            certifications=detail.certifications if detail is not None else [],
        )
        matches = await self._retrieval_agent.retrieve(profile, DEFAULT_MATCH_COUNT)
        return MatchingResponse(profile=profile, matches=matches)

    async def _resolve_detail(
        self,
        user_id: UUID,
        request: MatchingRequest,
    ) -> UserDetail | None:
        if request.user_detail_id is None:
            return None
        detail = await self._details.get_by_id(request.user_detail_id)
        if detail is None:
            raise ResourceNotFoundError("User detail not found")
        if detail.user_id != user_id:
            raise ResourceAccessDeniedError("The selected document does not belong to this user")
        if detail.document_type != DocumentType.RESUME.value:
            raise InvalidDocumentSelectionError("Only a parsed resume can be used for matching")
        return detail

    @staticmethod
    def _merge_skills(profile_skills: list[str], selected_skills: list[str]) -> list[str]:
        unique_skills: dict[str, str] = {}
        for skill in [*profile_skills, *selected_skills]:
            normalized = skill.strip()
            if normalized:
                unique_skills.setdefault(normalized.casefold(), normalized)
        return list(unique_skills.values())
