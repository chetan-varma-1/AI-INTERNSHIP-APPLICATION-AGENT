"""Auth FastAPI dependencies."""

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import JWTService
from app.auth.service import AuthService
from app.core.config import Settings, get_settings
from app.core.exceptions import UnauthorizedError
from app.database.connection import get_db
from app.database.repositories.user_repository import UserRepository
from app.schemas.auth import UserPublic


def get_jwt_service(settings: Settings = Depends(get_settings)) -> JWTService:
    """Provide a JWTService instance."""
    return JWTService(settings)


def get_auth_service(
    db: AsyncSession = Depends(get_db),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> AuthService:
    """Provide an AuthService wired to the current DB session."""
    return AuthService(UserRepository(db), jwt_service)


async def get_current_user(
    request: Request,
    settings: Settings = Depends(get_settings),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserPublic:
    """Resolve the logged-in user from the access-token HTTP-only cookie."""
    token = request.cookies.get(settings.access_cookie_name)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        return await auth_service.get_current_user(token)
    except UnauthorizedError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
