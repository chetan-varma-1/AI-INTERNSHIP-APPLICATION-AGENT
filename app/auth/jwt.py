"""JWT access and refresh token helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID

import jwt

from app.core.config import Settings

TokenType = Literal["access", "refresh"]


class TokenError(Exception):
    """Raised when a JWT cannot be verified."""


class JWTService:
    """Create and verify access/refresh JWTs."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def create_access_token(self, user_id: UUID, email: str) -> str:
        """Create a short-lived access token."""
        return self._encode(
            user_id=user_id,
            email=email,
            token_type="access",
            expires_delta=timedelta(minutes=self._settings.access_token_expire_minutes),
        )

    def create_refresh_token(self, user_id: UUID, email: str) -> str:
        """Create a longer-lived refresh token."""
        return self._encode(
            user_id=user_id,
            email=email,
            token_type="refresh",
            expires_delta=timedelta(days=self._settings.refresh_token_expire_days),
        )

    def decode_token(self, token: str, expected_type: TokenType) -> dict[str, Any]:
        """Verify a JWT and ensure it has the expected type claim."""
        try:
            payload = jwt.decode(
                token,
                self._settings.jwt_secret_key,
                algorithms=[self._settings.jwt_algorithm],
            )
        except jwt.PyJWTError as exc:
            raise TokenError("Invalid or expired token") from exc

        if payload.get("type") != expected_type:
            raise TokenError("Invalid token type")
        if "sub" not in payload:
            raise TokenError("Token missing subject")
        return payload

    def _encode(
        self,
        *,
        user_id: UUID,
        email: str,
        token_type: TokenType,
        expires_delta: timedelta,
    ) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "email": email,
            "type": token_type,
            "iat": now,
            "exp": now + expires_delta,
        }
        return jwt.encode(
            payload,
            self._settings.jwt_secret_key,
            algorithm=self._settings.jwt_algorithm,
        )
