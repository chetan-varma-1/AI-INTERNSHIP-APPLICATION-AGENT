"""User profile summary business logic."""

from __future__ import annotations

from uuid import UUID

from app.core.exceptions import ResourceNotFoundError
from app.database.repositories.user_repository import UserRepository
from app.schemas.user_detail import ProfileSummaryResponse


class ProfileService:
    """Build matching-ready summaries from user and profile records."""

    def __init__(self, user_repository: UserRepository) -> None:
        self._users = user_repository

    async def create_summary(self, user_id: UUID) -> ProfileSummaryResponse:
        """Return a concise summary of a user's stored profile."""
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise ResourceNotFoundError("User not found")

        location = user.profile.location_preference if user.profile else None
        skills = user.profile.skills if user.profile else []
        location_text = location or "any location"
        skills_text = ", ".join(skills) if skills else "no skills listed"
        summary = (
            f"{user.name} is seeking internship opportunities in {location_text}. "
            f"Current skills: {skills_text}."
        )
        return ProfileSummaryResponse(
            user_id=user.id,
            name=user.name,
            email=user.email,
            location_preference=location,
            skills=skills,
            profile_summary=summary,
        )
