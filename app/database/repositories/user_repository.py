"""User persistence for authentication."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User, UserProfile


class UserRepository:
    """Data-access layer for users and profiles."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a user by email, including profile."""
        stmt = select(User).options(selectinload(User.profile)).where(User.email == email.lower())
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Fetch a user by id, including profile."""
        stmt = select(User).options(selectinload(User.profile)).where(User.id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        name: str,
        email: str,
        password_hash: str,
        location_preference: str | None,
        skills: list[str],
    ) -> User:
        """Persist a new user and optional profile fields."""
        user = User(name=name.strip(), email=email.lower(), password_hash=password_hash)
        user.profile = UserProfile(
            location_preference=location_preference,
            skills=skills,
        )
        self._session.add(user)
        await self._session.flush()
        return user
