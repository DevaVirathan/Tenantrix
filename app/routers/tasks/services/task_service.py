"""Tasks service — business logic for the tasks domain."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.task import Task, TaskPriority, TaskStatus
from app.db.models.task_label import TaskLabel
from app.routers.tasks.repositories.task_repo import (
    get_active_membership,
    get_label_by_name,
    get_or_create_label,
    get_project_by_id,
    get_task_label_link,
    load_task,
)
from app.routers.tasks.schemas.task_schemas import LabelOut, TaskOut
from app.services.audit import write_audit


def _get_project_or_404(db, org_id, project_id):
    project = get_project_by_id(db, project_id)
    if project is None or project.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return project


def _get_task_or_404(db: Session, org_id: uuid.UUID, task_id: uuid.UUID) -> Task:
    task = load_task(db, org_id, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    return task


def _task_to_out(task: Task) -> TaskOut:
    labels = [LabelOut.model_validate(tl.label) for tl in task.task_labels]
    return TaskOut(
        id=task.id, organization_id=task.organization_id, project_id=task.project_id,
        assignee_user_id=task.assignee_user_id, title=task.title, description=task.description,
        status=task.status, priority=task.priority, position=task.position, labels=labels,
        deleted_at=task.deleted_at, created_at=task.created_at, updated_at=task.updated_at,
    )


def create_task(
    db: Session,
    *,
    org_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    project_id: uuid.UUID,
    title: str,
    description: str | None,
    task_status: TaskStatus,
    priority: TaskPriority,
    assignee_user_id: uuid.UUID | None,
    position: int,
) -> TaskOut:
    _get_project_or_404(db, org_id, project_id)
    if assignee_user_id is not None and get_active_membership(db, org_id, assignee_user_id) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Assignee is not an active member of this organisation.",
        )
    task = Task(
        organization_id=org_id,
        project_id=project_id,
        title=title,
        description=description,
        status=task_status,
        priority=priority,
        assignee_user_id=assignee_user_id,
        position=position,
    )
    db.add(task)
    db.flush()
    write_audit(
        db,
        organization_id=org_id,
        actor_user_id=actor_user_id,
        action="task.created",
        resource_type="task",
        resource_id=str(task.id),
        metadata={"title": task.title, "project_id": str(project_id)},
    )
    db.commit()
    db.expire_all()
    return _task_to_out(_get_task_or_404(db, org_id, task.id))


def list_tasks(
    db: Session,
    *,
    org_id: uuid.UUID,
    project_id: uuid.UUID,
    task_status=None,
    priority=None,
    assignee_user_id=None,
) -> list[TaskOut]:
    from sqlalchemy.orm import selectinload

    from app.db.models.task_label import TaskLabel

    _get_project_or_404(db, org_id, project_id)
    q = (
        select(Task)
        .where(Task.project_id == project_id, Task.organization_id == org_id, Task.deleted_at.is_(None))
        .options(selectinload(Task.task_labels).selectinload(TaskLabel.label))
        .order_by(Task.position, Task.created_at)
    )
    if task_status is not None:
        q = q.where(Task.status == task_status)
    if priority is not None:
        q = q.where(Task.priority == priority)
    if assignee_user_id is not None:
        q = q.where(Task.assignee_user_id == assignee_user_id)
    return [_task_to_out(t) for t in db.scalars(q).all()]


def get_task(db: Session, org_id: uuid.UUID, task_id: uuid.UUID) -> TaskOut:
    return _task_to_out(_get_task_or_404(db, org_id, task_id))


def update_task(
    db: Session,
    *,
    org_id: uuid.UUID,
    task_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    body,
) -> TaskOut:
    task = _get_task_or_404(db, org_id, task_id)
    if body.title is not None:
        task.title = body.title
    if body.description is not None:
        task.description = body.description
    if body.status is not None:
        task.status = body.status
    if body.priority is not None:
        task.priority = body.priority
    if body.position is not None:
        task.position = body.position
    if "assignee_user_id" in body.model_fields_set:
        if body.assignee_user_id is not None and get_active_membership(db, org_id, body.assignee_user_id) is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Assignee is not an active member of this organisation.",
            )
        task.assignee_user_id = body.assignee_user_id
    write_audit(
        db,
        organization_id=org_id,
        actor_user_id=actor_user_id,
        action="task.updated",
        resource_type="task",
        resource_id=str(task_id),
    )
    db.commit()
    db.expire_all()
    return _task_to_out(_get_task_or_404(db, org_id, task.id))


def delete_task(db: Session, *, org_id: uuid.UUID, task_id: uuid.UUID, actor_user_id: uuid.UUID) -> None:
    task = _get_task_or_404(db, org_id, task_id)
    task.deleted_at = datetime.now(UTC)
    write_audit(db, organization_id=org_id, actor_user_id=actor_user_id, action="task.deleted", resource_type="task", resource_id=str(task_id))
    db.commit()


def add_label(db: Session, *, org_id: uuid.UUID, task_id: uuid.UUID, actor_user_id: uuid.UUID, name: str, color: str | None) -> TaskOut:
    task = _get_task_or_404(db, org_id, task_id)
    label = get_or_create_label(db, org_id, name, color)
    if get_task_label_link(db, task.id, label.id) is None:
        db.add(TaskLabel(task_id=task.id, label_id=label.id))
    write_audit(db, organization_id=org_id, actor_user_id=actor_user_id, action="task.label_added", resource_type="task", resource_id=str(task.id), metadata={"label": name})
    db.commit()
    db.expire_all()
    return _task_to_out(_get_task_or_404(db, org_id, task.id))


def remove_label(db: Session, *, org_id: uuid.UUID, task_id: uuid.UUID, actor_user_id: uuid.UUID, label_name: str) -> None:
    task = _get_task_or_404(db, org_id, task_id)
    label = get_label_by_name(db, org_id, label_name)
    if label is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Label not found.")
    link = get_task_label_link(db, task.id, label.id)
    if link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Label not attached to this task.")
    db.delete(link)
    write_audit(db, organization_id=org_id, actor_user_id=actor_user_id, action="task.label_removed", resource_type="task", resource_id=str(task.id), metadata={"label": label_name})
    db.commit()
