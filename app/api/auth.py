"""Auth HTTP routes: signup, login, refresh, logout, me."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.auth.cookies import CookieManager
from app.auth.dependencies import get_auth_service, get_current_user
from app.auth.service import AuthService
from app.core.config import Settings, get_settings
from app.core.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    UnauthorizedError,
)
from app.schemas.auth import (
    AuthMessageResponse,
    LoginRequest,
    MessageResponse,
    SignupRequest,
    UserPublic,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def get_cookie_manager(settings: Settings = Depends(get_settings)) -> CookieManager:
    """Provide cookie helper bound to app settings."""
    return CookieManager(settings)


@router.post("/signup", response_model=AuthMessageResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    payload: SignupRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    cookies: CookieManager = Depends(get_cookie_manager),
) -> AuthMessageResponse:
    """Create an account and set auth cookies."""
    try:
        user, tokens = await auth_service.signup(payload)
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    cookies.set_auth_cookies(response, tokens)
    return AuthMessageResponse(message="Signup successful", user=user)


@router.post("/login", response_model=AuthMessageResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    cookies: CookieManager = Depends(get_cookie_manager),
) -> AuthMessageResponse:
    """Authenticate and set auth cookies."""
    try:
        user, tokens = await auth_service.login(payload)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    cookies.set_auth_cookies(response, tokens)
    return AuthMessageResponse(message="Login successful", user=user)


@router.post("/refresh", response_model=MessageResponse)
async def refresh(
    request: Request,
    response: Response,
    settings: Settings = Depends(get_settings),
    auth_service: AuthService = Depends(get_auth_service),
    cookies: CookieManager = Depends(get_cookie_manager),
) -> MessageResponse:
    """Issue a new token pair from the refresh-token cookie."""
    refresh_token = request.cookies.get(settings.refresh_cookie_name)
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        tokens = await auth_service.refresh(refresh_token)
    except UnauthorizedError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    cookies.set_auth_cookies(response, tokens)
    return MessageResponse(message="Token refreshed")


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    cookies: CookieManager = Depends(get_cookie_manager),
) -> MessageResponse:
    """Clear auth cookies."""
    cookies.clear_auth_cookies(response)
    return MessageResponse(message="Logout successful")


@router.get("/me", response_model=UserPublic)
async def me(current_user: UserPublic = Depends(get_current_user)) -> UserPublic:
    """Return the authenticated user's profile."""
    return current_user
