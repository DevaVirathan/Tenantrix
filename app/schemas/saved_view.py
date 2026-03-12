"""Pydantic schemas for saved view endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SavedViewCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    filters: dict[str, Any] = Field(default_factory=dict)
    view_type: str = Field("board", pattern=r"^(board|list|calendar|timeline)$")
    is_shared: bool = False


class SavedViewUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    filters: dict[str, Any] | None = None
    view_type: str | None = Field(None, pattern=r"^(board|list|calendar|timeline)$")
    is_shared: bool | None = None


class SavedViewOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    organization_id: uuid.UUID
    created_by_user_id: uuid.UUID
    name: str
    description: str | None
    filters: dict[str, Any]
    view_type: str
    is_shared: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
