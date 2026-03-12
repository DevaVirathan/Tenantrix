"""Project analytics endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Path
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import OrgMember
from app.db.session import get_db
from app.models.project_state import ProjectState, StateGroup
from app.models.sprint import Sprint
from app.models.task import Task, TaskStatus

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

    # Count by custom state
    state_rows = db.execute(
        select(ProjectState.id, ProjectState.name, ProjectState.color, func.count(Task.id))
        .outerjoin(Task, (Task.state_id == ProjectState.id) & Task.deleted_at.is_(None))
        .where(ProjectState.project_id == project_id)
        .group_by(ProjectState.id, ProjectState.name, ProjectState.color)
        .order_by(ProjectState.position)
    ).all()
    by_state = [
        {"id": str(row[0]), "name": row[1], "color": row[2], "count": row[3]}
        for row in state_rows
    ]

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

    # Sprint summaries — recent sprints with task/point counts
    sprint_rows = db.execute(
        select(Sprint).where(
            Sprint.project_id == project_id,
            Sprint.organization_id == org.id,
        ).order_by(Sprint.created_at.desc()).limit(10)
    ).scalars().all()

    sprint_summaries = []
    for sprint in sprint_rows:
        s_total = db.scalar(
            select(func.count(Task.id)).where(
                Task.sprint_id == sprint.id, Task.deleted_at.is_(None),
            )
        ) or 0
        s_done = db.scalar(
            select(func.count(Task.id))
            .join(ProjectState, ProjectState.id == Task.state_id)
            .where(
                Task.sprint_id == sprint.id,
                Task.deleted_at.is_(None),
                ProjectState.group == StateGroup.COMPLETED,
            )
        ) or 0
        s_points = db.scalar(
            select(func.coalesce(func.sum(Task.story_points), 0)).where(
                Task.sprint_id == sprint.id, Task.deleted_at.is_(None),
            )
        ) or 0
        s_done_points = db.scalar(
            select(func.coalesce(func.sum(Task.story_points), 0))
            .join(ProjectState, ProjectState.id == Task.state_id)
            .where(
                Task.sprint_id == sprint.id,
                Task.deleted_at.is_(None),
                ProjectState.group == StateGroup.COMPLETED,
            )
        ) or 0
        sprint_summaries.append({
            "id": str(sprint.id),
            "name": sprint.name,
            "status": sprint.status,
            "start_date": sprint.start_date.isoformat() if sprint.start_date else None,
            "end_date": sprint.end_date.isoformat() if sprint.end_date else None,
            "total_tasks": s_total,
            "done_tasks": s_done,
            "total_points": s_points,
            "done_points": s_done_points,
        })

    return {
        "total_tasks": total,
        "total_points": total_points,
        "done_points": done_points,
        "by_status": by_status,
        "by_state": by_state,
        "by_priority": by_priority,
        "by_assignee": by_assignee,
        "sprints": sprint_summaries,
    }
