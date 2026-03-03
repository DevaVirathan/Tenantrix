"""Pydantic schemas for the auth endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


# --------------------------------------------------------------------------- #
# Request bodies                                                              #
# --------------------------------------------------------------------------- #
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)

    @field_validator("password")
    @classmethod
    def password_not_too_simple(cls, v: str) -> str:
        if v.isdigit() or v.isalpha():
            raise ValueError("Password must contain letters and numbers.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


# --------------------------------------------------------------------------- #
# Response bodies                                                             #
# --------------------------------------------------------------------------- #
class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenPair(BaseModel):
    """Returned on login and refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access token expires


class AccessTokenOut(BaseModel):
    """Returned on /refresh — new access token only (+ new refresh token)."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class MessageOut(BaseModel):
    message: str
