"""Project management endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from app.api.deps import OrgAdmin, OrgMember
from app.db.session import get_db
from app.routers.projects.schemas.project_schemas import (
    ProjectCreateRequest,
    ProjectOut,
    ProjectUpdateRequest,
)
from app.routers.projects.services.project_service import (
    create_project,
    delete_project,
    get_project,
    list_projects,
    update_project,
)

router = APIRouter(prefix="/organizations/{org_id}/projects", tags=["projects"])


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project_endpoint(
    body: ProjectCreateRequest,
    org_member: OrgMember,
    db: Session = Depends(get_db),  # noqa: B008
):
    org, membership = org_member
    return create_project(db, org_id=org.id, actor_user_id=membership.user_id, name=body.name, description=body.description, status_val=body.status)


@router.get("", response_model=list[ProjectOut])
def list_projects_endpoint(
    org_member: OrgMember,
    db: Session = Depends(get_db),  # noqa: B008
):
    org, _ = org_member
    return list_projects(db, org.id)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project_endpoint(
    org_member: OrgMember,
    project_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    org, _ = org_member
    return get_project(db, org.id, project_id)


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project_endpoint(
    body: ProjectUpdateRequest,
    org_admin: OrgAdmin,
    project_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    org, membership = org_admin
    return update_project(db, org_id=org.id, project_id=project_id, actor_user_id=membership.user_id, name=body.name, description=body.description, status_val=body.status)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_endpoint(
    org_admin: OrgAdmin,
    project_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    org, membership = org_admin
    delete_project(db, org_id=org.id, project_id=project_id, actor_user_id=membership.user_id)
