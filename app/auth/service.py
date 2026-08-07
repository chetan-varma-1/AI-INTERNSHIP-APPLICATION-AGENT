"""Authentication business logic."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.auth.jwt import JWTService, TokenError
from app.auth.password import hash_password, verify_password
from app.core.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    UnauthorizedError,
)
from app.database.repositories.user_repository import UserRepository
from app.models.user import User
from app.schemas.auth import LoginRequest, SignupRequest, UserPublic


@dataclass(frozen=True)
class AuthTokens:
    """Pair of JWTs issued after signup/login/refresh."""

    access_token: str
    refresh_token: str


class AuthService:
    """Coordinates signup, login, refresh, and current-user flows."""

    def __init__(self, users: UserRepository, jwt_service: JWTService) -> None:
        self._users = users
        self._jwt = jwt_service

    async def signup(self, payload: SignupRequest) -> tuple[UserPublic, AuthTokens]:
        """Register a new user and issue auth tokens."""
        existing = await self._users.get_by_email(payload.email)
        if existing is not None:
            raise EmailAlreadyRegisteredError("Email already registered")

        user = await self._users.create(
            name=payload.name,
            email=payload.email,
            password_hash=hash_password(payload.password),
            location_preference=payload.location_preference,
            skills=payload.skills,
        )
        return self._to_public(user), self._issue_tokens(user)

    async def login(self, payload: LoginRequest) -> tuple[UserPublic, AuthTokens]:
        """Authenticate a user and issue auth tokens."""
        user = await self._users.get_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise InvalidCredentialsError("Invalid credentials")
        return self._to_public(user), self._issue_tokens(user)

    async def refresh(self, refresh_token: str) -> AuthTokens:
        """Validate a refresh token and issue a new access/refresh pair."""
        try:
            claims = self._jwt.decode_token(refresh_token, expected_type="refresh")
            user_id = UUID(claims["sub"])
        except (TokenError, ValueError, KeyError) as exc:
            raise UnauthorizedError("Invalid refresh token") from exc

        user = await self._users.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("Invalid refresh token")
        return self._issue_tokens(user)

    async def get_current_user(self, access_token: str) -> UserPublic:
        """Resolve the authenticated user from an access token."""
        try:
            claims = self._jwt.decode_token(access_token, expected_type="access")
            user_id = UUID(claims["sub"])
        except (TokenError, ValueError, KeyError) as exc:
            raise UnauthorizedError("Could not validate credentials") from exc

        user = await self._users.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("Could not validate credentials")
        return self._to_public(user)

    def _issue_tokens(self, user: User) -> AuthTokens:
        return AuthTokens(
            access_token=self._jwt.create_access_token(user.id, user.email),
            refresh_token=self._jwt.create_refresh_token(user.id, user.email),
        )

    @staticmethod
    def _to_public(user: User) -> UserPublic:
        profile = user.profile
        return UserPublic(
            id=user.id,
            name=user.name,
            email=user.email,
            location_preference=profile.location_preference if profile else None,
            skills=list(profile.skills) if profile and profile.skills else [],
        )
