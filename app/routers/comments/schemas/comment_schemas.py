"""Pydantic schemas for the comments domain."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CommentCreateRequest(BaseModel):
    body: str = Field(..., min_length=1, max_length=10_000)


class CommentUpdateRequest(BaseModel):
    body: str = Field(..., min_length=1, max_length=10_000)


class CommentOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    task_id: uuid.UUID
    author_user_id: uuid.UUID | None
    body: str
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
