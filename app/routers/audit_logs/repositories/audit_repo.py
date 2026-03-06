"""Audit logs repository — DB queries for the audit_logs domain."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.audit_log import AuditLog


def query_audit_logs(
    db: Session,
    *,
    org_id: uuid.UUID,
    action: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    actor_user_id: uuid.UUID | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[AuditLog]:
    q = select(AuditLog).where(AuditLog.organization_id == org_id).order_by(AuditLog.created_at.desc())
    if action is not None:
        q = q.where(AuditLog.action == action)
    if resource_type is not None:
        q = q.where(AuditLog.resource_type == resource_type)
    if resource_id is not None:
        q = q.where(AuditLog.resource_id == resource_id)
    if actor_user_id is not None:
        q = q.where(AuditLog.actor_user_id == actor_user_id)
    if since is not None:
        q = q.where(AuditLog.created_at >= since)
    if until is not None:
        q = q.where(AuditLog.created_at <= until)
    q = q.offset(offset).limit(limit)
    return list(db.scalars(q).all())
