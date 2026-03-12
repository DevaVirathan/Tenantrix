"""Audit log endpoints — M7."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import OrgAdmin, OrgMember
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogOut

router = APIRouter(prefix="/organizations/{org_id}", tags=["audit-logs"])

_MAX_PAGE_SIZE = 100
_DEFAULT_PAGE_SIZE = 50


# --------------------------------------------------------------------------- #
# GET /organizations/{org_id}/audit-logs                                       #
# --------------------------------------------------------------------------- #


@router.get("/audit-logs", response_model=list[AuditLogOut])
def list_audit_logs(
    org_admin: OrgAdmin,
    db: Session = Depends(get_db),  # noqa: B008
    action: str | None = Query(None, description="Filter by exact action string"),
    resource_type: str | None = Query(None),
    resource_id: str | None = Query(None),
    actor_user_id: uuid.UUID | None = Query(None),  # noqa: B008
    since: datetime | None = Query(None, description="ISO-8601 — return entries after this timestamp"),  # noqa: B008
    until: datetime | None = Query(None, description="ISO-8601 — return entries before this timestamp"),  # noqa: B008
    limit: int = Query(_DEFAULT_PAGE_SIZE, ge=1, le=_MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0),
) -> list[AuditLogOut]:
    """Return audit events for an organisation — newest first (ADMIN+ required)."""
    org, _membership = org_admin

    q = (
        select(AuditLog)
        .where(AuditLog.organization_id == org.id)
        .order_by(AuditLog.created_at.desc())
    )

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

    rows = db.scalars(q).all()
    return [AuditLogOut.from_orm(r) for r in rows]


# --------------------------------------------------------------------------- #
# GET /organizations/{org_id}/tasks/{task_id}/activity                         #
# --------------------------------------------------------------------------- #


@router.get("/tasks/{task_id}/activity", response_model=list[AuditLogOut])
def list_task_activity(
    org_member: OrgMember,
    task_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
    limit: int = Query(100, ge=1, le=_MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0),
) -> list[AuditLogOut]:
    """Return audit events for a specific task — any member can view."""
    org, _membership = org_member

    q = (
        select(AuditLog)
        .where(
            AuditLog.organization_id == org.id,
            AuditLog.resource_type == "task",
            AuditLog.resource_id == str(task_id),
        )
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    rows = db.scalars(q).all()
    return [AuditLogOut.from_orm(r) for r in rows]
