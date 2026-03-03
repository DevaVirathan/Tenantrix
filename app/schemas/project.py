"""Pydantic schemas for project endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.project import ProjectStatus

# --------------------------------------------------------------------------- #
# Request schemas                                                               #
# --------------------------------------------------------------------------- #


class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    status: ProjectStatus = ProjectStatus.ACTIVE


class ProjectUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    status: ProjectStatus | None = None


# --------------------------------------------------------------------------- #
# Response schemas                                                              #
# --------------------------------------------------------------------------- #


class ProjectOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: str | None
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
