"""Pydantic schemas for M7 — Audit Logs."""

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
        # metadata_ is the ORM column name; expose as metadata in the API
        return cls(
            id=obj.id,  # type: ignore[attr-defined]
            organization_id=obj.organization_id,  # type: ignore[attr-defined]
            actor_user_id=obj.actor_user_id,  # type: ignore[attr-defined]
            action=obj.action,  # type: ignore[attr-defined]
            resource_type=obj.resource_type,  # type: ignore[attr-defined]
            resource_id=obj.resource_id,  # type: ignore[attr-defined]
            metadata=obj.metadata_,  # type: ignore[attr-defined]
            created_at=obj.created_at,  # type: ignore[attr-defined]
        )
