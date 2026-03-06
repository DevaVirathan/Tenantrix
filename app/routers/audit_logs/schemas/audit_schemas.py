"""Pydantic schemas for the audit_logs domain."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    actor_user_id: uuid.UUID | None
    action: str
    resource_type: str | None
    resource_id: str | None
    metadata: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm(cls, obj: object) -> AuditLogOut:
        return cls(
            id=obj.id,
            organization_id=obj.organization_id,
            actor_user_id=obj.actor_user_id,
            action=obj.action,
            resource_type=obj.resource_type,
            resource_id=obj.resource_id,
            metadata=obj.metadata_,
            created_at=obj.created_at,
        )
