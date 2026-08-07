"""Auth request/response schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SignupRequest(BaseModel):
    """Payload for creating a new account."""

    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    location_preference: str | None = Field(default=None, max_length=120)
    skills: list[str] = Field(default_factory=list)


class LoginRequest(BaseModel):
    """Payload for authenticating an existing user."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserPublic(BaseModel):
    """Safe user representation returned to clients."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: EmailStr
    location_preference: str | None = None
    skills: list[str] = Field(default_factory=list)


class AuthMessageResponse(BaseModel):
    """Standard auth success payload."""

    message: str
    user: UserPublic


class MessageResponse(BaseModel):
    """Simple status message."""

    message: str
