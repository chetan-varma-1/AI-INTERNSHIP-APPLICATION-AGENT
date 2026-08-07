"""Unit tests for authentication (no PostgreSQL required)."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth.jwt import JWTService, TokenError
from app.auth.password import hash_password, verify_password
from app.auth.service import AuthService
from app.core.config import Settings
from app.core.exceptions import EmailAlreadyRegisteredError, InvalidCredentialsError
from app.models.user import User, UserProfile
from app.schemas.auth import LoginRequest, SignupRequest


@pytest.fixture
def settings() -> Settings:
    return Settings(
        jwt_secret_key="test-secret-key-at-least-32-bytes!!",
        access_token_expire_minutes=15,
        refresh_token_expire_days=7,
    )


@pytest.fixture
def jwt_service(settings: Settings) -> JWTService:
    return JWTService(settings)


def test_hash_and_verify_password() -> None:
    hashed = hash_password("Rahul@123")
    assert hashed != "Rahul@123"
    assert hashed.startswith("$2")
    assert verify_password("Rahul@123", hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_access_and_refresh_roundtrip(jwt_service: JWTService) -> None:
    user_id = uuid4()
    access = jwt_service.create_access_token(user_id, "rahul@gmail.com")
    refresh = jwt_service.create_refresh_token(user_id, "rahul@gmail.com")

    access_claims = jwt_service.decode_token(access, expected_type="access")
    refresh_claims = jwt_service.decode_token(refresh, expected_type="refresh")

    assert access_claims["sub"] == str(user_id)
    assert access_claims["email"] == "rahul@gmail.com"
    assert access_claims["type"] == "access"
    assert "password" not in access_claims
    assert refresh_claims["type"] == "refresh"

    with pytest.raises(TokenError):
        jwt_service.decode_token(access, expected_type="refresh")


def _make_user(*, email: str = "rahul@gmail.com", password: str = "Rahul@123") -> User:
    user = User(
        id=uuid4(),
        name="Rahul",
        email=email,
        password_hash=hash_password(password),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    user.profile = UserProfile(
        id=uuid4(),
        user_id=user.id,
        location_preference="Hyderabad",
        skills=["Python", "FastAPI", "SQL"],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    return user


@pytest.mark.asyncio
async def test_signup_success(jwt_service: JWTService) -> None:
    repo = AsyncMock()
    repo.get_by_email.return_value = None
    created = _make_user()
    repo.create.return_value = created

    service = AuthService(repo, jwt_service)
    public, tokens = await service.signup(
        SignupRequest(
            name="Rahul",
            email="rahul@gmail.com",
            password="Rahul@123",
            location_preference="Hyderabad",
            skills=["Python", "FastAPI", "SQL"],
        )
    )

    assert public.email == "rahul@gmail.com"
    assert public.skills == ["Python", "FastAPI", "SQL"]
    assert tokens.access_token
    assert tokens.refresh_token
    repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_signup_duplicate_email(jwt_service: JWTService) -> None:
    repo = AsyncMock()
    repo.get_by_email.return_value = _make_user()
    service = AuthService(repo, jwt_service)

    with pytest.raises(EmailAlreadyRegisteredError):
        await service.signup(
            SignupRequest(name="Rahul", email="rahul@gmail.com", password="Rahul@123")
        )


@pytest.mark.asyncio
async def test_login_success_and_failure(jwt_service: JWTService) -> None:
    user = _make_user()
    repo = AsyncMock()
    repo.get_by_email.return_value = user
    service = AuthService(repo, jwt_service)

    public, tokens = await service.login(
        LoginRequest(email="rahul@gmail.com", password="Rahul@123")
    )
    assert public.name == "Rahul"
    assert tokens.access_token

    with pytest.raises(InvalidCredentialsError):
        await service.login(LoginRequest(email="rahul@gmail.com", password="WrongPass1"))


@pytest.mark.asyncio
async def test_get_current_user_from_access_token(jwt_service: JWTService) -> None:
    user = _make_user()
    repo = AsyncMock()
    repo.get_by_id.return_value = user
    service = AuthService(repo, jwt_service)

    token = jwt_service.create_access_token(user.id, user.email)
    public = await service.get_current_user(token)
    assert public.id == user.id
    assert public.location_preference == "Hyderabad"


def test_auth_routes_with_overrides(jwt_service: JWTService, settings: Settings) -> None:
    """Exercise route wiring with dependency overrides (no real DB)."""
    from app.api.auth import router
    from app.auth.dependencies import get_auth_service, get_current_user
    from app.auth.service import AuthTokens
    from app.core.config import get_settings
    from app.schemas.auth import UserPublic

    user = UserPublic(
        id=uuid4(),
        name="Rahul",
        email="rahul@gmail.com",
        location_preference="Hyderabad",
        skills=["Python"],
    )
    tokens = AuthTokens(access_token="access", refresh_token="refresh")

    mock_service = AsyncMock()
    mock_service.signup.return_value = (user, tokens)
    mock_service.login.return_value = (user, tokens)
    mock_service.refresh.return_value = tokens

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_auth_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: user

    client = TestClient(app)

    signup = client.post(
        "/auth/signup",
        json={
            "name": "Rahul",
            "email": "rahul@gmail.com",
            "password": "Rahul@123",
            "location_preference": "Hyderabad",
            "skills": ["Python", "FastAPI"],
        },
    )
    assert signup.status_code == 201
    assert signup.json()["message"] == "Signup successful"
    assert "access_token" in signup.cookies

    login = client.post(
        "/auth/login",
        json={"email": "rahul@gmail.com", "password": "Rahul@123"},
    )
    assert login.status_code == 200
    assert login.json()["user"]["email"] == "rahul@gmail.com"

    me = client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["name"] == "Rahul"

    logout = client.post("/auth/logout")
    assert logout.status_code == 200
    assert logout.json()["message"] == "Logout successful"
