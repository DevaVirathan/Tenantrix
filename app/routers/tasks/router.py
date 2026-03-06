"""Task management endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.api.deps import OrgAdmin, OrgMember
from app.db.models.task import TaskPriority, TaskStatus
from app.db.session import get_db
from app.routers.tasks.schemas.task_schemas import (
    LabelCreateRequest,
    TaskCreateRequest,
    TaskOut,
    TaskUpdateRequest,
)
from app.routers.tasks.services.task_service import (
    add_label,
    create_task,
    delete_task,
    get_task,
    list_tasks,
    remove_label,
    update_task,
)

router = APIRouter(prefix="/organizations/{org_id}", tags=["tasks"])


@router.post("/projects/{project_id}/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task_endpoint(
    body: TaskCreateRequest,
    org_member: OrgMember,
    project_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    org, membership = org_member
    return create_task(
        db,
        org_id=org.id,
        actor_user_id=membership.user_id,
        project_id=project_id,
        title=body.title,
        description=body.description,
        task_status=body.status,
        priority=body.priority,
        assignee_user_id=body.assignee_user_id,
        position=body.position,
    )


@router.get("/projects/{project_id}/tasks", response_model=list[TaskOut])
def list_tasks_endpoint(
    org_member: OrgMember,
    project_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
    task_status: TaskStatus | None = Query(None, alias="status"),  # noqa: B008
    priority: TaskPriority | None = Query(None),  # noqa: B008
    assignee_user_id: uuid.UUID | None = Query(None),  # noqa: B008
):
    org, _ = org_member
    return list_tasks(db, org_id=org.id, project_id=project_id, task_status=task_status, priority=priority, assignee_user_id=assignee_user_id)


@router.get("/tasks/{task_id}", response_model=TaskOut)
def get_task_endpoint(
    org_member: OrgMember,
    task_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    org, _ = org_member
    return get_task(db, org.id, task_id)


@router.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task_endpoint(
    body: TaskUpdateRequest,
    org_member: OrgMember,
    task_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    org, membership = org_member
    return update_task(db, org_id=org.id, task_id=task_id, actor_user_id=membership.user_id, body=body)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_endpoint(
    org_admin: OrgAdmin,
    task_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    org, membership = org_admin
    delete_task(db, org_id=org.id, task_id=task_id, actor_user_id=membership.user_id)


@router.post("/tasks/{task_id}/labels", response_model=TaskOut, status_code=status.HTTP_200_OK)
def add_label_endpoint(
    body: LabelCreateRequest,
    org_member: OrgMember,
    task_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    org, membership = org_member
    return add_label(db, org_id=org.id, task_id=task_id, actor_user_id=membership.user_id, name=body.name, color=body.color)


@router.delete("/tasks/{task_id}/labels/{label_name}", status_code=status.HTTP_204_NO_CONTENT)
def remove_label_endpoint(
    org_member: OrgMember,
    task_id: uuid.UUID = Path(...),  # noqa: B008
    label_name: str = Path(...),
    db: Session = Depends(get_db),  # noqa: B008
):
    org, membership = org_member
    remove_label(db, org_id=org.id, task_id=task_id, actor_user_id=membership.user_id, label_name=label_name)
