"""Pydantic schemas for sprint endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.sprint import SprintStatus


class SprintCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    start_date: datetime | None = None
    end_date: datetime | None = None
    goals: str | None = Field(None, max_length=2000)


class SprintUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    status: SprintStatus | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    goals: str | None = None


class SprintOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    project_id: uuid.UUID
    name: str
    description: str | None
    status: SprintStatus
    start_date: datetime | None
    end_date: datetime | None
    goals: str | None
    task_count: int = 0
    done_count: int = 0
    total_points: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
