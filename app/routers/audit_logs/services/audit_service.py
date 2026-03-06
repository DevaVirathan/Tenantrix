"""Audit logs service."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models.audit_log import AuditLog
from app.routers.audit_logs.repositories.audit_repo import query_audit_logs


def list_audit_logs(db: Session, *, org_id: uuid.UUID, action: str | None = None, resource_type: str | None = None, resource_id: str | None = None, actor_user_id: uuid.UUID | None = None, since: datetime | None = None, until: datetime | None = None, limit: int = 50, offset: int = 0) -> list[AuditLog]:
    return query_audit_logs(db, org_id=org_id, action=action, resource_type=resource_type, resource_id=resource_id, actor_user_id=actor_user_id, since=since, until=until, limit=limit, offset=offset)
