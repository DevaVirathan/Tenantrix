"""Pydantic schemas for attachment endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class AttachmentOut(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    organization_id: uuid.UUID
    uploaded_by_user_id: uuid.UUID
    filename: str
    file_size: int
    mime_type: str
    s3_key: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
