"""Pydantic schemas for project state endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.project_state import StateGroup


class StateCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field("#6b7280", pattern=r"^#[0-9A-Fa-f]{6}$")
    group: StateGroup
    position: int = Field(0, ge=0)
    is_default: bool = False


class StateUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50)
    color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    group: StateGroup | None = None
    position: int | None = Field(None, ge=0)
    is_default: bool | None = None


class StateReorderRequest(BaseModel):
    """List of state IDs in the desired order."""
    state_ids: list[uuid.UUID]


class StateOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    color: str
    group: StateGroup
    position: int
    is_default: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
