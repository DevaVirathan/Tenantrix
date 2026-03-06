"""Audit log endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import OrgAdmin
from app.db.session import get_db
from app.routers.audit_logs.schemas.audit_schemas import AuditLogOut
from app.routers.audit_logs.services.audit_service import list_audit_logs

router = APIRouter(prefix="/organizations/{org_id}", tags=["audit-logs"])

_MAX_PAGE_SIZE = 100
_DEFAULT_PAGE_SIZE = 50


@router.get("/audit-logs", response_model=list[AuditLogOut])
def list_audit_logs_endpoint(
    org_admin: OrgAdmin,
    db: Session = Depends(get_db),  # noqa: B008
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    resource_id: str | None = Query(None),
    actor_user_id: uuid.UUID | None = Query(None),  # noqa: B008
    since: datetime | None = Query(None),  # noqa: B008
    until: datetime | None = Query(None),  # noqa: B008
    limit: int = Query(_DEFAULT_PAGE_SIZE, ge=1, le=_MAX_PAGE_SIZE),
    offset: int = Query(0, ge=0),
) -> list[AuditLogOut]:
    org, _ = org_admin
    rows = list_audit_logs(db, org_id=org.id, action=action, resource_type=resource_type, resource_id=resource_id, actor_user_id=actor_user_id, since=since, until=until, limit=limit, offset=offset)
    return [AuditLogOut.from_orm(r) for r in rows]
