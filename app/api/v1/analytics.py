"""Project analytics endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Path
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import OrgMember
from app.db.session import get_db
from app.models.task import Task, TaskPriority, TaskStatus

router = APIRouter(prefix="/organizations/{org_id}", tags=["analytics"])


@router.get("/projects/{project_id}/analytics")
def project_analytics(
    org_member: OrgMember,
    project_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> dict:
    """Return analytics data for a project (MEMBER+ required)."""
    org, _membership = org_member

    base = select(Task).where(
        Task.project_id == project_id,
        Task.organization_id == org.id,
        Task.deleted_at.is_(None),
    )

    # Count by status
    status_rows = db.execute(
        select(Task.status, func.count(Task.id))
        .where(Task.project_id == project_id, Task.organization_id == org.id, Task.deleted_at.is_(None))
        .group_by(Task.status)
    ).all()
    by_status = {str(row[0]): row[1] for row in status_rows}

    # Count by priority
    priority_rows = db.execute(
        select(Task.priority, func.count(Task.id))
        .where(Task.project_id == project_id, Task.organization_id == org.id, Task.deleted_at.is_(None))
        .group_by(Task.priority)
    ).all()
    by_priority = {str(row[0]): row[1] for row in priority_rows}

    # Count by assignee
    assignee_rows = db.execute(
        select(Task.assignee_user_id, func.count(Task.id))
        .where(Task.project_id == project_id, Task.organization_id == org.id, Task.deleted_at.is_(None))
        .group_by(Task.assignee_user_id)
    ).all()
    by_assignee = {str(row[0]) if row[0] else "unassigned": row[1] for row in assignee_rows}

    # Total counts
    total = db.scalar(
        select(func.count(Task.id)).where(
            Task.project_id == project_id, Task.organization_id == org.id, Task.deleted_at.is_(None)
        )
    ) or 0
    total_points = db.scalar(
        select(func.coalesce(func.sum(Task.story_points), 0)).where(
            Task.project_id == project_id, Task.organization_id == org.id, Task.deleted_at.is_(None)
        )
    ) or 0
    done_points = db.scalar(
        select(func.coalesce(func.sum(Task.story_points), 0)).where(
            Task.project_id == project_id, Task.organization_id == org.id,
            Task.deleted_at.is_(None), Task.status == TaskStatus.DONE,
        )
    ) or 0

    return {
        "total_tasks": total,
        "total_points": total_points,
        "done_points": done_points,
        "by_status": by_status,
        "by_priority": by_priority,
        "by_assignee": by_assignee,
    }
