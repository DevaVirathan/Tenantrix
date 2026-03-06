"""Pydantic schemas for organization endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.membership import OrgRole

# --------------------------------------------------------------------------- #
# Request schemas                                                               #
# --------------------------------------------------------------------------- #


class OrgCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: str | None = Field(None, max_length=1000)


class OrgUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)


class InviteCreateRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    role: OrgRole = OrgRole.MEMBER

    @field_validator("email")
    @classmethod
    def email_lower(cls, v: str) -> str:
        return v.strip().lower()


class MemberRoleUpdateRequest(BaseModel):
    role: OrgRole


# --------------------------------------------------------------------------- #
# Response schemas                                                              #
# --------------------------------------------------------------------------- #


class OrgOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    created_by_user_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MemberOut(BaseModel):
    user_id: uuid.UUID
    role: OrgRole
    status: str
    joined_at: datetime  # maps to created_at on the Membership row

    model_config = {"from_attributes": True}


class InviteOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    email: str
    role: OrgRole
    token: str
    expires_at: datetime

    model_config = {"from_attributes": True}
