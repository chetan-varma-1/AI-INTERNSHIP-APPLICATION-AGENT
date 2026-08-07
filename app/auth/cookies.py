"""HTTP-only cookie helpers for JWT tokens."""

from datetime import timedelta
from typing import Literal, cast

from fastapi import Response

from app.auth.service import AuthTokens
from app.core.config import Settings

SameSite = Literal["lax", "strict", "none"]


class CookieManager:
    """Sets and clears access/refresh token cookies."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._samesite = cast(SameSite, settings.cookie_samesite.lower())

    def set_auth_cookies(self, response: Response, tokens: AuthTokens) -> None:
        """Attach access and refresh tokens as HTTP-only cookies."""
        self._set_cookie(
            response,
            name=self._settings.access_cookie_name,
            value=tokens.access_token,
            max_age=int(timedelta(minutes=self._settings.access_token_expire_minutes).total_seconds()),
        )
        self._set_cookie(
            response,
            name=self._settings.refresh_cookie_name,
            value=tokens.refresh_token,
            max_age=int(timedelta(days=self._settings.refresh_token_expire_days).total_seconds()),
        )

    def clear_auth_cookies(self, response: Response) -> None:
        """Expire access and refresh cookies."""
        response.delete_cookie(
            key=self._settings.access_cookie_name,
            path="/",
            samesite=self._samesite,
            secure=self._settings.cookie_secure,
            httponly=True,
        )
        response.delete_cookie(
            key=self._settings.refresh_cookie_name,
            path="/",
            samesite=self._samesite,
            secure=self._settings.cookie_secure,
            httponly=True,
        )

    def _set_cookie(self, response: Response, *, name: str, value: str, max_age: int) -> None:
        response.set_cookie(
            key=name,
            value=value,
            max_age=max_age,
            httponly=True,
            secure=self._settings.cookie_secure,
            samesite=self._samesite,
            path="/",
        )
