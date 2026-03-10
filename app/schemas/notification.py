"""Pydantic schemas for notification endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: uuid.UUID
    recipient_user_id: uuid.UUID
    actor_user_id: uuid.UUID | None
    organization_id: uuid.UUID
    action_type: str
    resource_type: str
    resource_id: str
    message: str
    read_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UnreadCountOut(BaseModel):
    count: int
