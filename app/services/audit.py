"""Audit log service — thin write helper used by all M3-M7 endpoints."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def write_audit(
    db: Session,
    *,
    organization_id: uuid.UUID,
    actor_user_id: uuid.UUID | None,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    metadata: dict | None = None,
) -> AuditLog:
    """Insert an immutable audit event and flush (caller must commit)."""
    entry = AuditLog(
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        metadata_=metadata,
    )
    db.add(entry)
    db.flush()
    return entry
