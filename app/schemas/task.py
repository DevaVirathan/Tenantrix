"""Pydantic schemas for task and label endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.task import TaskPriority, TaskStatus

# --------------------------------------------------------------------------- #
# Label schemas                                                                 #
# --------------------------------------------------------------------------- #


class LabelCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class LabelOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    color: str | None

    model_config = {"from_attributes": True}


# --------------------------------------------------------------------------- #
# Task request schemas                                                          #
# --------------------------------------------------------------------------- #


class TaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = Field(None, max_length=5000)
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee_user_id: uuid.UUID | None = None
    position: int = Field(0, ge=0)


class TaskUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assignee_user_id: uuid.UUID | None = None
    position: int | None = Field(None, ge=0)


# --------------------------------------------------------------------------- #
# Task response schema                                                          #
# --------------------------------------------------------------------------- #


class TaskOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    project_id: uuid.UUID
    assignee_user_id: uuid.UUID | None
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    position: int
    labels: list[LabelOut] = []
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
