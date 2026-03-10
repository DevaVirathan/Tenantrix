"""Pydantic schemas for module endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.module import ModuleStatus


class ModuleCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    start_date: datetime | None = None
    end_date: datetime | None = None


class ModuleUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    status: ModuleStatus | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


class ModuleOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    project_id: uuid.UUID
    name: str
    description: str | None
    status: ModuleStatus
    start_date: datetime | None
    end_date: datetime | None
    task_count: int = 0
    done_count: int = 0
    total_points: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
