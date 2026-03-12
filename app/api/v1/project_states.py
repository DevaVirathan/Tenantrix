"""Project state management endpoints — custom workflow states per project."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import func as sa_func, select
from sqlalchemy.orm import Session

from app.api.deps import OrgAdmin, OrgMember
from app.db.session import get_db
from app.models.project import Project
from app.models.project_state import ProjectState
from app.schemas.project_state import (
    StateCreateRequest,
    StateOut,
    StateReorderRequest,
    StateUpdateRequest,
)
from app.services.audit import write_audit

router = APIRouter(prefix="/organizations/{org_id}", tags=["project-states"])


# --------------------------------------------------------------------------- #
# Helpers                                                                       #
# --------------------------------------------------------------------------- #


def _get_project_or_404(db: Session, org_id: uuid.UUID, project_id: uuid.UUID) -> Project:
    project = db.get(Project, project_id)
    if project is None or project.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return project


# --------------------------------------------------------------------------- #
# GET /projects/{project_id}/states — list                                     #
# --------------------------------------------------------------------------- #


@router.get("/projects/{project_id}/states", response_model=list[StateOut])
def list_states(
    org_member: OrgMember,
    project_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> list[ProjectState]:
    """List all states for a project, ordered by position (MEMBER+ required)."""
    org, _membership = org_member
    _get_project_or_404(db, org.id, project_id)
    return list(
        db.scalars(
            select(ProjectState)
            .where(ProjectState.project_id == project_id)
            .order_by(ProjectState.position)
        ).all()
    )


# --------------------------------------------------------------------------- #
# POST /projects/{project_id}/states — create                                  #
# --------------------------------------------------------------------------- #


@router.post("/projects/{project_id}/states", response_model=StateOut, status_code=status.HTTP_201_CREATED)
def create_state(
    body: StateCreateRequest,
    org_admin: OrgAdmin,
    project_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> ProjectState:
    """Create a new state in the project (ADMIN+ required)."""
    org, membership = org_admin
    _get_project_or_404(db, org.id, project_id)

    # If this is set as default, unset others
    if body.is_default:
        for s in db.scalars(select(ProjectState).where(ProjectState.project_id == project_id, ProjectState.is_default.is_(True))):
            s.is_default = False

    state = ProjectState(
        project_id=project_id,
        name=body.name,
        color=body.color,
        group=body.group,
        position=body.position,
        is_default=body.is_default,
    )
    db.add(state)
    db.flush()
    write_audit(
        db,
        organization_id=org.id,
        actor_user_id=membership.user_id,
        action="state.created",
        resource_type="project_state",
        resource_id=str(state.id),
        metadata={"name": state.name, "group": state.group.value, "project_id": str(project_id)},
    )
    db.commit()
    db.refresh(state)
    return state


# --------------------------------------------------------------------------- #
# PATCH /states/{state_id} — update                                            #
# --------------------------------------------------------------------------- #


@router.patch("/states/{state_id}", response_model=StateOut)
def update_state(
    body: StateUpdateRequest,
    org_admin: OrgAdmin,
    state_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> ProjectState:
    """Update a project state (ADMIN+ required)."""
    org, membership = org_admin
    state = db.get(ProjectState, state_id)
    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="State not found.")
    # Verify project belongs to this org
    project = db.get(Project, state.project_id)
    if project is None or project.organization_id != org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="State not found.")

    if body.name is not None:
        state.name = body.name
    if body.color is not None:
        state.color = body.color
    if body.group is not None:
        state.group = body.group
    if body.position is not None:
        state.position = body.position
    if body.is_default is not None:
        if body.is_default:
            # Unset other defaults in this project
            for s in db.scalars(select(ProjectState).where(
                ProjectState.project_id == state.project_id,
                ProjectState.is_default.is_(True),
                ProjectState.id != state.id,
            )):
                s.is_default = False
        state.is_default = body.is_default

    write_audit(
        db,
        organization_id=org.id,
        actor_user_id=membership.user_id,
        action="state.updated",
        resource_type="project_state",
        resource_id=str(state_id),
        metadata={"name": state.name},
    )
    db.commit()
    db.refresh(state)
    return state


# --------------------------------------------------------------------------- #
# DELETE /states/{state_id} — delete                                           #
# --------------------------------------------------------------------------- #


@router.delete("/states/{state_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_state(
    org_admin: OrgAdmin,
    state_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> None:
    """Delete a project state (ADMIN+ required). Cannot delete if tasks are using it."""
    org, membership = org_admin
    state = db.get(ProjectState, state_id)
    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="State not found.")
    project = db.get(Project, state.project_id)
    if project is None or project.organization_id != org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="State not found.")

    # Check if any tasks are using this state
    from app.models.task import Task
    task_count = db.scalar(
        select(sa_func.count()).select_from(Task).where(Task.state_id == state_id, Task.deleted_at.is_(None))
    )
    if task_count and task_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete state — {task_count} work item(s) are using it. Move them first.",
        )

    write_audit(
        db,
        organization_id=org.id,
        actor_user_id=membership.user_id,
        action="state.deleted",
        resource_type="project_state",
        resource_id=str(state_id),
        metadata={"name": state.name},
    )
    db.delete(state)
    db.commit()


# --------------------------------------------------------------------------- #
# PATCH /projects/{project_id}/states/reorder                                  #
# --------------------------------------------------------------------------- #


@router.patch("/projects/{project_id}/states/reorder", response_model=list[StateOut])
def reorder_states(
    body: StateReorderRequest,
    org_admin: OrgAdmin,
    project_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> list[ProjectState]:
    """Reorder all states in a project (ADMIN+ required)."""
    org, _membership = org_admin
    _get_project_or_404(db, org.id, project_id)

    states = {
        s.id: s
        for s in db.scalars(
            select(ProjectState).where(ProjectState.project_id == project_id)
        ).all()
    }

    for position, state_id in enumerate(body.state_ids):
        if state_id in states:
            states[state_id].position = position

    db.commit()
    return list(
        db.scalars(
            select(ProjectState)
            .where(ProjectState.project_id == project_id)
            .order_by(ProjectState.position)
        ).all()
    )
