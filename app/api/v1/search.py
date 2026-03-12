"""Global search endpoint — PostgreSQL full-text search."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select, text
from sqlalchemy.orm import Session

from app.api.deps import OrgMember
from app.db.session import get_db
from app.models.project import Project
from app.models.project_state import ProjectState
from app.models.task import Task

router = APIRouter(prefix="/organizations/{org_id}", tags=["search"])


@router.get("/search")
def global_search(
    org_member: OrgMember,
    q: str = Query(..., min_length=1, max_length=200),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> dict:
    """Search across tasks and projects using full-text search with ILIKE fallback."""
    org, _membership = org_member
    pattern = f"%{q}%"

    # Build tsquery from user input — plainto_tsquery handles special characters safely
    ts_query = func.plainto_tsquery("english", q)

    # Full-text search on task title + description, ranked by relevance
    ts_vector = func.to_tsvector(
        "english",
        func.coalesce(Task.title, "") + text("' '") + func.coalesce(Task.description, ""),
    )
    ts_rank = func.ts_rank(ts_vector, ts_query)

    task_rows = db.execute(
        select(Task, Project.name, Project.identifier, ProjectState.name, ProjectState.color, ts_rank.label("rank"))
        .join(Project, Project.id == Task.project_id)
        .outerjoin(ProjectState, ProjectState.id == Task.state_id)
        .where(
            Task.organization_id == org.id,
            Task.deleted_at.is_(None),
            or_(
                ts_vector.bool_op("@@")(ts_query),
                Task.title.ilike(pattern),
            ),
        )
        .order_by(ts_rank.desc())
        .limit(20)
    ).all()

    tasks = [
        {
            "id": str(row[0].id),
            "type": "task",
            "title": row[0].title,
            "status": row[0].status,
            "project_id": str(row[0].project_id),
            "project_name": row[1],
            "identifier": row[2],
            "sequence_id": row[0].sequence_id,
            "state_name": row[3],
            "state_color": row[4],
        }
        for row in task_rows
    ]

    # Search projects with full-text + ILIKE fallback
    proj_ts = func.to_tsvector(
        "english",
        func.coalesce(Project.name, "") + text("' '") + func.coalesce(Project.description, ""),
    )
    project_rows = db.scalars(
        select(Project)
        .where(
            Project.organization_id == org.id,
            or_(
                proj_ts.bool_op("@@")(ts_query),
                Project.name.ilike(pattern),
            ),
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
