"""Project management endpoints — M4."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import OrgAdmin, OrgMember
from app.db.session import get_db
from app.models.project import Project
from app.schemas.project import ProjectCreateRequest, ProjectOut, ProjectUpdateRequest
from app.services.audit import write_audit

router = APIRouter(prefix="/organizations/{org_id}/projects", tags=["projects"])


# --------------------------------------------------------------------------- #
# Helper                                                                        #
# --------------------------------------------------------------------------- #


def _get_project_or_404(db: Session, org_id: uuid.UUID, project_id: uuid.UUID) -> Project:
    project = db.get(Project, project_id)
    if project is None or project.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return project


# --------------------------------------------------------------------------- #
# POST /organizations/{org_id}/projects — create                                #
# --------------------------------------------------------------------------- #


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    body: ProjectCreateRequest,
    org_member: OrgMember,
    db: Session = Depends(get_db),  # noqa: B008
) -> Project:
    """Create a new project in the organisation (MEMBER+ required)."""
    org, membership = org_member
    project = Project(
        organization_id=org.id,
        name=body.name,
        description=body.description,
        status=body.status,
    )
    db.add(project)
    db.flush()
    write_audit(
        db,
        organization_id=org.id,
        actor_user_id=membership.user_id,
        action="project.created",
        resource_type="project",
        resource_id=str(project.id),
        metadata={"name": project.name},
    )
    db.commit()
    db.refresh(project)
    return project


# --------------------------------------------------------------------------- #
# GET /organizations/{org_id}/projects — list                                   #
# --------------------------------------------------------------------------- #


@router.get("", response_model=list[ProjectOut])
def list_projects(
    org_member: OrgMember,
    db: Session = Depends(get_db),  # noqa: B008
) -> list[Project]:
    """List all projects in the organisation (MEMBER+ required)."""
    org, _membership = org_member
    projects = db.scalars(
        select(Project)
        .where(Project.organization_id == org.id)
        .order_by(Project.created_at.desc())
    ).all()
    return list(projects)


# --------------------------------------------------------------------------- #
# GET /organizations/{org_id}/projects/{project_id} — retrieve                 #
# --------------------------------------------------------------------------- #


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    org_member: OrgMember,
    project_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> Project:
    """Retrieve a single project (MEMBER+ required)."""
    org, _membership = org_member
    return _get_project_or_404(db, org.id, project_id)


# --------------------------------------------------------------------------- #
# PATCH /organizations/{org_id}/projects/{project_id} — update                 #
# --------------------------------------------------------------------------- #


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    body: ProjectUpdateRequest,
    org_admin: OrgAdmin,
    project_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> Project:
    """Update a project's name / description / status (ADMIN+ required)."""
    org, membership = org_admin
    project = _get_project_or_404(db, org.id, project_id)

    if body.name is not None:
        project.name = body.name
    if body.description is not None:
        project.description = body.description
    if body.status is not None:
        project.status = body.status

    write_audit(
        db,
        organization_id=org.id,
        actor_user_id=membership.user_id,
        action="project.updated",
        resource_type="project",
        resource_id=str(project_id),
    )
    db.commit()
    db.refresh(project)
    return project


# --------------------------------------------------------------------------- #
# DELETE /organizations/{org_id}/projects/{project_id} — delete                #
# --------------------------------------------------------------------------- #


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    org_admin: OrgAdmin,
    project_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> None:
    """Delete a project and all its tasks (ADMIN+ required)."""
    org, membership = org_admin
    project = _get_project_or_404(db, org.id, project_id)
    db.delete(project)
    write_audit(
        db,
        organization_id=org.id,
        actor_user_id=membership.user_id,
        action="project.deleted",
        resource_type="project",
        resource_id=str(project_id),
        metadata={"name": project.name},
    )
    db.commit()
