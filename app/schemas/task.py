"""Pydantic schemas for task and label endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.project_state import StateGroup
from app.models.task import IssueType, TaskPriority, TaskStatus
from app.models.task_link import LinkType

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
    state_id: uuid.UUID | None = None
    status: TaskStatus = TaskStatus.TODO  # legacy fallback
    priority: TaskPriority = TaskPriority.MEDIUM
    issue_type: IssueType = IssueType.TASK
    assignee_user_id: uuid.UUID | None = None
    parent_task_id: uuid.UUID | None = None
    sprint_id: uuid.UUID | None = None
    module_id: uuid.UUID | None = None
    position: int = Field(0, ge=0)
    story_points: int | None = Field(None, ge=0, le=100)
    start_date: datetime | None = None
    due_date: datetime | None = None


class TaskUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    state_id: uuid.UUID | None = None
    status: TaskStatus | None = None  # legacy fallback
    priority: TaskPriority | None = None
    issue_type: IssueType | None = None
    assignee_user_id: uuid.UUID | None = None
    parent_task_id: uuid.UUID | None = None
    sprint_id: uuid.UUID | None = None
    module_id: uuid.UUID | None = None
    position: int | None = Field(None, ge=0)
    story_points: int | None = Field(None, ge=0, le=100)
    start_date: datetime | None = None
    due_date: datetime | None = None


# --------------------------------------------------------------------------- #
# Task response schema                                                          #
# --------------------------------------------------------------------------- #


class TaskStateOut(BaseModel):
    """Embedded state info in task responses."""
    id: uuid.UUID
    name: str
    color: str
    group: StateGroup

    model_config = {"from_attributes": True}


class TaskSummary(BaseModel):
    """Lightweight task reference for parent/subtask/link contexts."""
    id: uuid.UUID
    title: str
    status: TaskStatus
    issue_type: IssueType
    sequence_id: int | None = None
    state: TaskStateOut | None = None

    model_config = {"from_attributes": True}


class TaskLinkOut(BaseModel):
    id: uuid.UUID
    link_type: LinkType
    source_task: TaskSummary
    target_task: TaskSummary
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskLinkCreateRequest(BaseModel):
    target_task_id: uuid.UUID
    link_type: LinkType


# --------------------------------------------------------------------------- #
# Bulk update schema                                                             #
# --------------------------------------------------------------------------- #


class BulkTaskUpdates(BaseModel):
    state_id: uuid.UUID | None = None
    priority: TaskPriority | None = None
    assignee_user_id: uuid.UUID | None = None
    sprint_id: uuid.UUID | None = None


class BulkUpdateRequest(BaseModel):
    task_ids: list[uuid.UUID] = Field(..., min_length=1, max_length=500)
    updates: BulkTaskUpdates


class BulkUpdateResponse(BaseModel):
    updated_count: int


# --------------------------------------------------------------------------- #
# CSV import response schema                                                     #
# --------------------------------------------------------------------------- #


class CSVImportResponse(BaseModel):
    imported_count: int
    errors: list[str] = []


class TaskOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    project_id: uuid.UUID
    assignee_user_id: uuid.UUID | None
    created_by_user_id: uuid.UUID | None = None
    parent_task_id: uuid.UUID | None
    sprint_id: uuid.UUID | None
    module_id: uuid.UUID | None
    state_id: uuid.UUID | None = None
    sequence_id: int | None = None
    title: str
    description: str | None
    state: TaskStateOut | None = None
    status: TaskStatus
    priority: TaskPriority
    issue_type: IssueType
    position: int
    story_points: int | None
    start_date: datetime | None
    due_date: datetime | None
    labels: list[LabelOut] = []
    parent: TaskSummary | None = None
    subtasks: list[TaskSummary] = []
    links: list[TaskLinkOut] = []
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
