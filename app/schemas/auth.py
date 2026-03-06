"""Pydantic schemas for the auth endpoints."""

from __future__ import annotations

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

_SPECIAL_RE = re.compile(r"[!@#$%^&*()\-_=+\[\]{};:'\",.<>/?\\|`~]")


# --------------------------------------------------------------------------- #
# Request bodies                                                              #
# --------------------------------------------------------------------------- #
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        errors: list[str] = []
        if not any(c.islower() for c in v):
            errors.append("at least one lowercase letter")
        if not any(c.isupper() for c in v):
            errors.append("at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            errors.append("at least one digit")
        if not _SPECIAL_RE.search(v):
            errors.append("at least one special character (!@#$%^&* …)")
        if errors:
            raise ValueError("Password must contain: " + ", ".join(errors) + ".")
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
