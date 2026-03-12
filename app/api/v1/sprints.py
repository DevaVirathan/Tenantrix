"""Sprint management endpoints — agile iteration planning."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import OrgAdmin, OrgMember
from app.db.session import get_db
from app.models.project import Project
from app.models.project_state import ProjectState, StateGroup
from app.models.sprint import Sprint, SprintStatus
from app.models.task import Task
from app.schemas.sprint import SprintCreateRequest, SprintOut, SprintUpdateRequest
from app.services.audit import write_audit

router = APIRouter(prefix="/organizations/{org_id}", tags=["sprints"])


# --------------------------------------------------------------------------- #
# Helpers                                                                       #
# --------------------------------------------------------------------------- #


def _get_project_or_404(db: Session, org_id: uuid.UUID, project_id: uuid.UUID) -> Project:
    project = db.get(Project, project_id)
    if project is None or project.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return project


def _sprint_to_out(db: Session, sprint: Sprint) -> SprintOut:
    """Build SprintOut with computed task_count, done_count, total_points."""
    row = db.execute(
        select(
            func.count(Task.id).label("task_count"),
            func.coalesce(func.sum(Task.story_points), 0).label("total_points"),
        ).where(Task.sprint_id == sprint.id, Task.deleted_at.is_(None))
    ).one()

    done_count = db.scalar(
        select(func.count(Task.id))
        .join(ProjectState, ProjectState.id == Task.state_id)
        .where(
            Task.sprint_id == sprint.id,
            Task.deleted_at.is_(None),
            ProjectState.group == StateGroup.COMPLETED,
        )
    ) or 0

    return SprintOut(
        id=sprint.id,
        organization_id=sprint.organization_id,
        project_id=sprint.project_id,
        name=sprint.name,
        description=sprint.description,
        status=sprint.status,
        start_date=sprint.start_date,
        end_date=sprint.end_date,
        goals=sprint.goals,
        task_count=row.task_count,
        done_count=done_count,
        total_points=row.total_points,
        created_at=sprint.created_at,
        updated_at=sprint.updated_at,
    )


# --------------------------------------------------------------------------- #
# POST — create sprint                                                          #
# --------------------------------------------------------------------------- #


@router.post(
    "/projects/{project_id}/sprints",
    response_model=SprintOut,
    status_code=status.HTTP_201_CREATED,
)
def create_sprint(
    body: SprintCreateRequest,
    org_member: OrgMember,
    project_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> SprintOut:
    """Create a new sprint in the project (MEMBER+ required)."""
    org, _membership = org_member
    _get_project_or_404(db, org.id, project_id)

    sprint = Sprint(
        organization_id=org.id,
        project_id=project_id,
        name=body.name,
        description=body.description,
        start_date=body.start_date,
        end_date=body.end_date,
        goals=body.goals,
    )
    db.add(sprint)
    db.flush()
    write_audit(
        db,
        organization_id=org.id,
        actor_user_id=_membership.user_id,
        action="sprint.created",
        resource_type="sprint",
        resource_id=str(sprint.id),
        metadata={"name": sprint.name, "project_id": str(project_id)},
    )
    db.commit()
    db.refresh(sprint)
    return _sprint_to_out(db, sprint)


# --------------------------------------------------------------------------- #
# GET — list sprints                                                            #
# --------------------------------------------------------------------------- #


@router.get("/projects/{project_id}/sprints", response_model=list[SprintOut])
def list_sprints(
    org_member: OrgMember,
    project_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
    sprint_status: SprintStatus | None = Query(None, alias="status"),  # noqa: B008
) -> list[SprintOut]:
    """List all sprints in a project (MEMBER+ required)."""
    org, _membership = org_member
    _get_project_or_404(db, org.id, project_id)

    q = select(Sprint).where(
        Sprint.project_id == project_id, Sprint.organization_id == org.id
    ).order_by(Sprint.created_at.desc())

    if sprint_status is not None:
        q = q.where(Sprint.status == sprint_status)

    sprints = db.scalars(q).all()
    return [_sprint_to_out(db, s) for s in sprints]


# --------------------------------------------------------------------------- #
# GET — get single sprint                                                       #
# --------------------------------------------------------------------------- #


@router.get("/sprints/{sprint_id}", response_model=SprintOut)
def get_sprint(
    org_member: OrgMember,
    sprint_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> SprintOut:
    """Retrieve a sprint by ID (MEMBER+ required)."""
    org, _membership = org_member
    sprint = db.get(Sprint, sprint_id)
    if sprint is None or sprint.organization_id != org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found.")
    return _sprint_to_out(db, sprint)


# --------------------------------------------------------------------------- #
# PATCH — update sprint (including start/close)                                 #
# --------------------------------------------------------------------------- #


@router.patch("/sprints/{sprint_id}", response_model=SprintOut)
def update_sprint(
    body: SprintUpdateRequest,
    org_member: OrgMember,
    sprint_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> SprintOut:
    """Update a sprint (MEMBER+ required). Use status='active' to start, 'closed' to close."""
    org, _membership = org_member
    sprint = db.get(Sprint, sprint_id)
    if sprint is None or sprint.organization_id != org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found.")

    # Enforce max 1 active sprint per project
    if body.status == SprintStatus.ACTIVE and sprint.status != SprintStatus.ACTIVE:
        existing_active = db.scalars(
            select(Sprint).where(
                Sprint.project_id == sprint.project_id,
                Sprint.status == SprintStatus.ACTIVE,
                Sprint.id != sprint.id,
            )
        ).first()
        if existing_active is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only one active sprint is allowed per project.",
            )

    if body.name is not None:
        sprint.name = body.name
    if body.description is not None:
        sprint.description = body.description
    if body.status is not None:
        sprint.status = body.status
    if "start_date" in body.model_fields_set:
        sprint.start_date = body.start_date
    if "end_date" in body.model_fields_set:
        sprint.end_date = body.end_date
    if body.goals is not None:
        sprint.goals = body.goals

    write_audit(
        db,
        organization_id=org.id,
        actor_user_id=_membership.user_id,
        action="sprint.updated",
        resource_type="sprint",
        resource_id=str(sprint_id),
    )
    db.commit()
    db.refresh(sprint)
    return _sprint_to_out(db, sprint)


# --------------------------------------------------------------------------- #
# DELETE — delete sprint (only if backlog and no tasks)                         #
# --------------------------------------------------------------------------- #


@router.delete("/sprints/{sprint_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sprint(
    org_admin: OrgAdmin,
    sprint_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> None:
    """Delete a sprint (ADMIN+ required). Only backlog sprints with no tasks can be deleted."""
    org, _membership = org_admin
    sprint = db.get(Sprint, sprint_id)
    if sprint is None or sprint.organization_id != org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found.")

    if sprint.status != SprintStatus.BACKLOG:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only backlog sprints can be deleted.",
        )

    task_count = db.scalar(
        select(func.count(Task.id)).where(Task.sprint_id == sprint.id, Task.deleted_at.is_(None))
    )
    if task_count and task_count > 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot delete a sprint that has tasks. Remove tasks first.",
        )

    write_audit(
        db,
        organization_id=org.id,
        actor_user_id=_membership.user_id,
        action="sprint.deleted",
        resource_type="sprint",
        resource_id=str(sprint_id),
    )
    db.delete(sprint)
    db.commit()
