"""Global search endpoint — PostgreSQL full-text search."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import OrgMember
from app.db.session import get_db
from app.models.project import Project
from app.models.task import Task

router = APIRouter(prefix="/organizations/{org_id}", tags=["search"])


@router.get("/search")
def global_search(
    org_member: OrgMember,
    q: str = Query(..., min_length=1, max_length=200),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> dict:
    """Search across tasks and projects in the organization."""
    org, _membership = org_member
    pattern = f"%{q}%"

    # Search tasks
    task_rows = db.scalars(
        select(Task)
        .where(
            Task.organization_id == org.id,
            Task.deleted_at.is_(None),
            or_(Task.title.ilike(pattern), Task.description.ilike(pattern)),
        )
        .limit(20)
    ).all()

    tasks = [
        {
            "id": str(t.id),
            "type": "task",
            "title": t.title,
            "status": t.status,
            "project_id": str(t.project_id),
        }
        for t in task_rows
    ]

    # Search projects
    project_rows = db.scalars(
        select(Project)
        .where(
            Project.organization_id == org.id,
            or_(Project.name.ilike(pattern), Project.description.ilike(pattern)),
        )
        .limit(10)
    ).all()

    projects = [
        {
            "id": str(p.id),
            "type": "project",
            "title": p.name,
            "description": p.description,
        }
        for p in project_rows
    ]

    return {"results": tasks + projects}
