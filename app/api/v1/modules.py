"""Module management endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import OrgAdmin, OrgMember
from app.db.session import get_db
from app.models.module import Module, ModuleStatus
from app.models.project import Project
from app.models.task import Task, TaskStatus
from app.schemas.module import ModuleCreateRequest, ModuleOut, ModuleUpdateRequest
from app.services.audit import write_audit

router = APIRouter(prefix="/organizations/{org_id}", tags=["modules"])


def _get_project_or_404(db: Session, org_id: uuid.UUID, project_id: uuid.UUID) -> Project:
    project = db.get(Project, project_id)
    if project is None or project.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return project


def _module_to_out(db: Session, module: Module) -> ModuleOut:
    row = db.execute(
        select(
            func.count(Task.id).label("task_count"),
            func.count(Task.id).filter(Task.status == TaskStatus.DONE).label("done_count"),
            func.coalesce(func.sum(Task.story_points), 0).label("total_points"),
        ).where(Task.module_id == module.id, Task.deleted_at.is_(None))
    ).one()
    return ModuleOut(
        id=module.id,
        organization_id=module.organization_id,
        project_id=module.project_id,
        name=module.name,
        description=module.description,
        status=module.status,
        start_date=module.start_date,
        end_date=module.end_date,
        task_count=row.task_count,
        done_count=row.done_count,
        total_points=row.total_points,
        created_at=module.created_at,
        updated_at=module.updated_at,
    )


@router.post(
    "/projects/{project_id}/modules",
    response_model=ModuleOut,
    status_code=status.HTTP_201_CREATED,
)
def create_module(
    body: ModuleCreateRequest,
    org_member: OrgMember,
    project_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> ModuleOut:
    org, _membership = org_member
    _get_project_or_404(db, org.id, project_id)
    module = Module(
        organization_id=org.id,
        project_id=project_id,
        name=body.name,
        description=body.description,
        start_date=body.start_date,
        end_date=body.end_date,
    )
    db.add(module)
    db.flush()
    write_audit(db, organization_id=org.id, actor_user_id=_membership.user_id,
                action="module.created", resource_type="module", resource_id=str(module.id),
                metadata={"name": module.name})
    db.commit()
    db.refresh(module)
    return _module_to_out(db, module)


@router.get("/projects/{project_id}/modules", response_model=list[ModuleOut])
def list_modules(
    org_member: OrgMember,
    project_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
    module_status: ModuleStatus | None = Query(None, alias="status"),  # noqa: B008
) -> list[ModuleOut]:
    org, _membership = org_member
    _get_project_or_404(db, org.id, project_id)
    q = select(Module).where(Module.project_id == project_id, Module.organization_id == org.id)
    if module_status is not None:
        q = q.where(Module.status == module_status)
    q = q.order_by(Module.created_at.desc())
    return [_module_to_out(db, m) for m in db.scalars(q).all()]


@router.patch("/modules/{module_id}", response_model=ModuleOut)
def update_module(
    body: ModuleUpdateRequest,
    org_member: OrgMember,
    module_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> ModuleOut:
    org, _membership = org_member
    module = db.get(Module, module_id)
    if module is None or module.organization_id != org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found.")
    if body.name is not None:
        module.name = body.name
    if body.description is not None:
        module.description = body.description
    if body.status is not None:
        module.status = body.status
    if "start_date" in body.model_fields_set:
        module.start_date = body.start_date
    if "end_date" in body.model_fields_set:
        module.end_date = body.end_date
    write_audit(db, organization_id=org.id, actor_user_id=_membership.user_id,
                action="module.updated", resource_type="module", resource_id=str(module_id))
    db.commit()
    db.refresh(module)
    return _module_to_out(db, module)


@router.delete("/modules/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_module(
    org_admin: OrgAdmin,
    module_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> None:
    org, _membership = org_admin
    module = db.get(Module, module_id)
    if module is None or module.organization_id != org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found.")
    # Unlink tasks from this module before deleting
    db.execute(
        select(Task).where(Task.module_id == module.id).execution_options(synchronize_session="fetch")
    )
    write_audit(db, organization_id=org.id, actor_user_id=_membership.user_id,
                action="module.deleted", resource_type="module", resource_id=str(module_id))
    db.delete(module)
    db.commit()
