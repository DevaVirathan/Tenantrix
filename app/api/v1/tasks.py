"""Task management endpoints — M5."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import OrgAdmin, OrgMember
from app.db.session import get_db
from app.models.label import Label
from app.models.membership import Membership
from app.models.project import Project
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.task_label import TaskLabel
from app.schemas.task import (
    LabelCreateRequest,
    LabelOut,
    TaskCreateRequest,
    TaskOut,
    TaskUpdateRequest,
)
from app.services.audit import write_audit

router = APIRouter(prefix="/organizations/{org_id}", tags=["tasks"])


# --------------------------------------------------------------------------- #
# Helpers                                                                       #
# --------------------------------------------------------------------------- #


def _get_project_or_404(db: Session, org_id: uuid.UUID, project_id: uuid.UUID) -> Project:
    project = db.get(Project, project_id)
    if project is None or project.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return project


def _load_task(db: Session, org_id: uuid.UUID, task_id: uuid.UUID) -> Task:
    """Load a task with its labels eagerly. Returns None if not found/deleted."""
    return db.scalars(
        select(Task)
        .where(Task.id == task_id, Task.organization_id == org_id, Task.deleted_at.is_(None))
        .options(selectinload(Task.task_labels).selectinload(TaskLabel.label))
    ).first()


def _get_task_or_404(db: Session, org_id: uuid.UUID, task_id: uuid.UUID) -> Task:
    task = _load_task(db, org_id, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    return task


def _task_to_out(task: Task) -> TaskOut:
    """Convert a Task ORM object (with task_labels loaded) to TaskOut."""
    labels = [LabelOut.model_validate(tl.label) for tl in task.task_labels]
    return TaskOut(
        id=task.id,
        organization_id=task.organization_id,
        project_id=task.project_id,
        assignee_user_id=task.assignee_user_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        position=task.position,
        labels=labels,
        deleted_at=task.deleted_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


# --------------------------------------------------------------------------- #
# POST /organizations/{org_id}/projects/{project_id}/tasks — create            #
# --------------------------------------------------------------------------- #


@router.post(
    "/projects/{project_id}/tasks",
    response_model=TaskOut,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    body: TaskCreateRequest,
    org_member: OrgMember,
    project_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> TaskOut:
    """Create a new task in the project (MEMBER+ required)."""
    org, _membership = org_member
    _get_project_or_404(db, org.id, project_id)

    # Validate assignee is a member of this org (if provided)
    if body.assignee_user_id is not None:
        membership = db.scalars(
            select(Membership).where(
                Membership.organization_id == org.id,
                Membership.user_id == body.assignee_user_id,
                Membership.status == "active",
            )
        ).first()
        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Assignee is not an active member of this organisation.",
            )

    task = Task(
        organization_id=org.id,
        project_id=project_id,
        title=body.title,
        description=body.description,
        status=body.status,
        priority=body.priority,
        assignee_user_id=body.assignee_user_id,
        position=body.position,
    )
    db.add(task)
    db.flush()
    write_audit(
        db,
        organization_id=org.id,
        actor_user_id=_membership.user_id,
        action="task.created",
        resource_type="task",
        resource_id=str(task.id),
        metadata={"title": task.title, "project_id": str(project_id)},
    )
    db.commit()
    db.expire_all()
    return _task_to_out(_get_task_or_404(db, org.id, task.id))


# --------------------------------------------------------------------------- #
# GET /organizations/{org_id}/projects/{project_id}/tasks — list               #
# --------------------------------------------------------------------------- #


@router.get("/projects/{project_id}/tasks", response_model=list[TaskOut])
def list_tasks(
    org_member: OrgMember,
    project_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
    task_status: TaskStatus | None = Query(None, alias="status"),  # noqa: B008
    priority: TaskPriority | None = Query(None),  # noqa: B008
    assignee_user_id: uuid.UUID | None = Query(None),  # noqa: B008
) -> list[TaskOut]:
    """List all active tasks in the project with optional filters (MEMBER+ required)."""
    org, _membership = org_member
    _get_project_or_404(db, org.id, project_id)

    q = (
        select(Task)
        .where(Task.project_id == project_id, Task.organization_id == org.id, Task.deleted_at.is_(None))
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


# --------------------------------------------------------------------------- #
# GET /organizations/{org_id}/tasks/{task_id} — retrieve                       #
# --------------------------------------------------------------------------- #


@router.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(
    org_member: OrgMember,
    task_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> TaskOut:
    """Retrieve a single task by ID (MEMBER+ required)."""
    org, _membership = org_member
    return _task_to_out(_get_task_or_404(db, org.id, task_id))


# --------------------------------------------------------------------------- #
# PATCH /organizations/{org_id}/tasks/{task_id} — update                       #
# --------------------------------------------------------------------------- #


@router.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(
    body: TaskUpdateRequest,
    org_member: OrgMember,
    task_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> TaskOut:
    """Update a task (MEMBER+ required — any member can update tasks)."""
    org, _membership = org_member
    task = _get_task_or_404(db, org.id, task_id)

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
        # Allow explicit null to unassign
        if body.assignee_user_id is not None:
            membership = db.scalars(
                select(Membership).where(
                    Membership.organization_id == org.id,
                    Membership.user_id == body.assignee_user_id,
                    Membership.status == "active",
                )
            ).first()
            if membership is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Assignee is not an active member of this organisation.",
                )
        task.assignee_user_id = body.assignee_user_id

    write_audit(
        db,
        organization_id=org.id,
        actor_user_id=_membership.user_id,
        action="task.updated",
        resource_type="task",
        resource_id=str(task_id),
    )
    db.commit()
    db.expire_all()
    return _task_to_out(_get_task_or_404(db, org.id, task.id))


# --------------------------------------------------------------------------- #
# DELETE /organizations/{org_id}/tasks/{task_id} — soft delete                 #
# --------------------------------------------------------------------------- #


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    org_admin: OrgAdmin,
    task_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> None:
    """Soft-delete a task (ADMIN+ required)."""
    org, _membership = org_admin
    task = _get_task_or_404(db, org.id, task_id)
    task.deleted_at = datetime.now(UTC)
    write_audit(
        db,
        organization_id=org.id,
        actor_user_id=_membership.user_id,
        action="task.deleted",
        resource_type="task",
        resource_id=str(task_id),
    )
    db.commit()


# --------------------------------------------------------------------------- #
# POST /organizations/{org_id}/tasks/{task_id}/labels — attach label           #
# --------------------------------------------------------------------------- #


@router.post("/tasks/{task_id}/labels", response_model=TaskOut, status_code=status.HTTP_200_OK)
def add_label_to_task(
    body: LabelCreateRequest,
    org_member: OrgMember,
    task_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> TaskOut:
    """Get-or-create a label by name and attach it to the task (MEMBER+ required)."""
    org, _membership = org_member
    task = _get_task_or_404(db, org.id, task_id)

    # Get or create label (upsert by org + name)
    label = db.scalars(
        select(Label).where(Label.organization_id == org.id, Label.name == body.name)
    ).first()
    if label is None:
        label = Label(organization_id=org.id, name=body.name, color=body.color)
        db.add(label)
        db.flush()  # get label.id without committing

    # Attach if not already attached
    existing_link = db.scalars(
        select(TaskLabel).where(TaskLabel.task_id == task.id, TaskLabel.label_id == label.id)
    ).first()
    if existing_link is None:
        db.add(TaskLabel(task_id=task.id, label_id=label.id))

    write_audit(
        db,
        organization_id=org.id,
        actor_user_id=_membership.user_id,
        action="task.label_added",
        resource_type="task",
        resource_id=str(task.id),
        metadata={"label": body.name},
    )
    db.commit()
    db.expire_all()  # clear identity map so reload fetches fresh data with selectinload
    return _task_to_out(_get_task_or_404(db, org.id, task.id))


# --------------------------------------------------------------------------- #
# DELETE /organizations/{org_id}/tasks/{task_id}/labels/{label_name} — detach  #
# --------------------------------------------------------------------------- #


@router.delete(
    "/tasks/{task_id}/labels/{label_name}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_label_from_task(
    org_member: OrgMember,
    task_id: uuid.UUID = Path(...),  # noqa: B008
    label_name: str = Path(...),
    db: Session = Depends(get_db),  # noqa: B008
) -> None:
    """Detach a label from a task by label name (MEMBER+ required)."""
    org, _membership = org_member
    task = _get_task_or_404(db, org.id, task_id)

    label = db.scalars(
        select(Label).where(Label.organization_id == org.id, Label.name == label_name)
    ).first()
    if label is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Label not found.")

    link = db.scalars(
        select(TaskLabel).where(TaskLabel.task_id == task.id, TaskLabel.label_id == label.id)
    ).first()
    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Label not attached to this task."
        )

    db.delete(link)
    write_audit(
        db,
        organization_id=org.id,
        actor_user_id=_membership.user_id,
        action="task.label_removed",
        resource_type="task",
        resource_id=str(task.id),
        metadata={"label": label_name},
    )
    db.commit()
