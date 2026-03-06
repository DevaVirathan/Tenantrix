"""Projects service — business logic for the projects domain."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.project import Project, ProjectStatus
from app.routers.projects.repositories.project_repo import get_project_by_id
from app.services.audit import write_audit


def _get_project_or_404(db: Session, org_id: uuid.UUID, project_id: uuid.UUID) -> Project:
    project = get_project_by_id(db, project_id)
    if project is None or project.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return project


def create_project(db: Session, *, org_id: uuid.UUID, actor_user_id: uuid.UUID, name: str, description: str | None, status_val: ProjectStatus) -> Project:
    project = Project(organization_id=org_id, name=name, description=description, status=status_val)
    db.add(project)
    db.flush()
    write_audit(db, organization_id=org_id, actor_user_id=actor_user_id, action="project.created", resource_type="project", resource_id=str(project.id), metadata={"name": project.name})
    db.commit()
    db.refresh(project)
    return project


def list_projects(db: Session, org_id: uuid.UUID) -> list[Project]:
    return list(db.scalars(select(Project).where(Project.organization_id == org_id).order_by(Project.created_at.desc())).all())


def get_project(db: Session, org_id: uuid.UUID, project_id: uuid.UUID) -> Project:
    return _get_project_or_404(db, org_id, project_id)


def update_project(db: Session, *, org_id: uuid.UUID, project_id: uuid.UUID, actor_user_id: uuid.UUID, name: str | None, description: str | None, status_val: ProjectStatus | None) -> Project:
    project = _get_project_or_404(db, org_id, project_id)
    if name is not None:
        project.name = name
    if description is not None:
        project.description = description
    if status_val is not None:
        project.status = status_val
    write_audit(db, organization_id=org_id, actor_user_id=actor_user_id, action="project.updated", resource_type="project", resource_id=str(project_id))
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, *, org_id: uuid.UUID, project_id: uuid.UUID, actor_user_id: uuid.UUID) -> None:
    project = _get_project_or_404(db, org_id, project_id)
    write_audit(db, organization_id=org_id, actor_user_id=actor_user_id, action="project.deleted", resource_type="project", resource_id=str(project_id))
    db.delete(project)
    db.commit()
