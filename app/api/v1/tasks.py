"""Task management endpoints — M5."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime  # noqa: TC003

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import OrgAdmin, OrgMember
from app.db.session import get_db
from app.models.label import Label
from app.models.membership import Membership
from app.models.project import Project
from app.models.task import IssueType, Task, TaskPriority, TaskStatus
from app.models.task_label import TaskLabel
from app.models.task_link import TaskLink
from app.schemas.task import (
    LabelCreateRequest,
    LabelOut,
    TaskCreateRequest,
    TaskLinkCreateRequest,
    TaskLinkOut,
    TaskOut,
    TaskSummary,
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
    """Load a task with labels, subtasks and links eagerly. Returns None if not found/deleted."""
    return db.scalars(
        select(Task)
        .where(Task.id == task_id, Task.organization_id == org_id, Task.deleted_at.is_(None))
        .options(
            selectinload(Task.task_labels).selectinload(TaskLabel.label),
            selectinload(Task.subtasks),
            selectinload(Task.parent),
            selectinload(Task.outbound_links).selectinload(TaskLink.target_task),
            selectinload(Task.inbound_links).selectinload(TaskLink.source_task),
        )
    ).first()


def _get_task_or_404(db: Session, org_id: uuid.UUID, task_id: uuid.UUID) -> Task:
    task = _load_task(db, org_id, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    return task


def _task_to_out(task: Task) -> TaskOut:
    """Convert a Task ORM object (with task_labels, subtasks, links loaded) to TaskOut."""
    labels = [LabelOut.model_validate(tl.label) for tl in task.task_labels]

    # Parent summary
    parent = TaskSummary.model_validate(task.parent) if task.parent else None

    # Active subtasks only
    subtask_list = [
        TaskSummary.model_validate(s) for s in (task.subtasks or []) if s.deleted_at is None
    ]

    # Merge outbound + inbound links
    links: list[TaskLinkOut] = []
    for lnk in (task.outbound_links or []):
        links.append(TaskLinkOut(
            id=lnk.id,
            link_type=lnk.link_type,
            source_task=TaskSummary.model_validate(task),
            target_task=TaskSummary.model_validate(lnk.target_task),
            created_at=lnk.created_at,
        ))
    for lnk in (task.inbound_links or []):
        links.append(TaskLinkOut(
            id=lnk.id,
            link_type=lnk.link_type,
            source_task=TaskSummary.model_validate(lnk.source_task),
            target_task=TaskSummary.model_validate(task),
            created_at=lnk.created_at,
        ))

    return TaskOut(
        id=task.id,
        organization_id=task.organization_id,
        project_id=task.project_id,
        assignee_user_id=task.assignee_user_id,
        created_by_user_id=task.created_by_user_id,
        parent_task_id=task.parent_task_id,
        sprint_id=task.sprint_id,
        module_id=task.module_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        issue_type=task.issue_type,
        position=task.position,
        story_points=task.story_points,
        start_date=task.start_date,
        due_date=task.due_date,
        labels=labels,
        parent=parent,
        subtasks=subtask_list,
        links=links,
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

    # Validate parent task exists in same org (if provided)
    if body.parent_task_id is not None:
        parent = _load_task(db, org.id, body.parent_task_id)
        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Parent task not found."
            )

    # Auto-set issue_type to subtask when parent is provided
    issue_type = body.issue_type
    if body.parent_task_id is not None and issue_type == IssueType.TASK:
        issue_type = IssueType.SUBTASK

    task = Task(
        organization_id=org.id,
        project_id=project_id,
        title=body.title,
        description=body.description,
        status=body.status,
        priority=body.priority,
        issue_type=issue_type,
        assignee_user_id=body.assignee_user_id,
        created_by_user_id=_membership.user_id,
        parent_task_id=body.parent_task_id,
        sprint_id=body.sprint_id,
        module_id=body.module_id,
        position=body.position,
        story_points=body.story_points,
        start_date=body.start_date,
        due_date=body.due_date,
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
    issue_type: IssueType | None = Query(None),  # noqa: B008
    sprint_id: uuid.UUID | None = Query(None),  # noqa: B008
    no_sprint: bool = Query(False),  # noqa: B008
    due_date_from: datetime | None = Query(None),  # noqa: B008
    due_date_to: datetime | None = Query(None),  # noqa: B008
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
    if issue_type is not None:
        q = q.where(Task.issue_type == issue_type)
    if sprint_id is not None:
        q = q.where(Task.sprint_id == sprint_id)
    elif no_sprint:
        q = q.where(Task.sprint_id.is_(None))
    if due_date_from is not None:
        q = q.where(Task.due_date >= due_date_from)
    if due_date_to is not None:
        q = q.where(Task.due_date <= due_date_to)

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
    if body.issue_type is not None:
        task.issue_type = body.issue_type
    if body.position is not None:
        task.position = body.position
    if "story_points" in body.model_fields_set:
        task.story_points = body.story_points
    if "start_date" in body.model_fields_set:
        task.start_date = body.start_date
    if "due_date" in body.model_fields_set:
        task.due_date = body.due_date
    if "parent_task_id" in body.model_fields_set:
        if body.parent_task_id is not None:
            if body.parent_task_id == task.id:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="A task cannot be its own parent.",
                )
            parent = _load_task(db, org.id, body.parent_task_id)
            if parent is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Parent task not found."
                )
        task.parent_task_id = body.parent_task_id
    if "sprint_id" in body.model_fields_set:
        task.sprint_id = body.sprint_id
    if "module_id" in body.model_fields_set:
        task.module_id = body.module_id
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

    # Write per-field audit logs for each changed field
    _FIELD_LABELS = {
        "title": "title", "description": "description", "status": "state",
        "priority": "priority", "issue_type": "type", "position": "position",
        "story_points": "estimate point", "start_date": "start date",
        "due_date": "due date", "sprint_id": "cycle", "module_id": "module",
        "assignee_user_id": "assignee", "parent_task_id": "parent",
    }
    for field_name in body.model_fields_set:
        new_value = getattr(body, field_name)
        field_label = _FIELD_LABELS.get(field_name, field_name)

        # Format display value
        if new_value is None:
            display_value = "none"
        elif isinstance(new_value, datetime):
            display_value = new_value.strftime("%b %d, %Y")
        elif hasattr(new_value, "value"):
            display_value = str(new_value.value)
        else:
            display_value = str(new_value)

        write_audit(
            db,
            organization_id=org.id,
            actor_user_id=_membership.user_id,
            action=f"task.field_updated",
            resource_type="task",
            resource_id=str(task_id),
            metadata={"field": field_label, "new_value": display_value},
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


# --------------------------------------------------------------------------- #
# POST /organizations/{org_id}/tasks/{task_id}/links — create task link       #
# --------------------------------------------------------------------------- #


@router.post("/tasks/{task_id}/links", response_model=TaskLinkOut, status_code=status.HTTP_201_CREATED)
def create_task_link(
    body: TaskLinkCreateRequest,
    org_member: OrgMember,
    task_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> TaskLinkOut:
    """Create a directional link between two tasks (MEMBER+ required)."""
    org, _membership = org_member
    source = _get_task_or_404(db, org.id, task_id)
    target = _load_task(db, org.id, body.target_task_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target task not found.")
    if source.id == target.id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cannot link a task to itself."
        )

    # Check for duplicate
    existing = db.scalars(
        select(TaskLink).where(
            TaskLink.source_task_id == source.id,
            TaskLink.target_task_id == target.id,
            TaskLink.link_type == body.link_type,
        )
    ).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Link already exists.")

    task_link = TaskLink(
        source_task_id=source.id,
        target_task_id=target.id,
        link_type=body.link_type,
        created_by_user_id=_membership.user_id,
    )
    db.add(task_link)
    db.flush()
    write_audit(
        db,
        organization_id=org.id,
        actor_user_id=_membership.user_id,
        action="task.link_created",
        resource_type="task",
        resource_id=str(source.id),
        metadata={"target_task_id": str(target.id), "link_type": body.link_type},
    )
    db.commit()
    db.refresh(task_link)
    return TaskLinkOut(
        id=task_link.id,
        link_type=task_link.link_type,
        source_task=TaskSummary.model_validate(source),
        target_task=TaskSummary.model_validate(target),
        created_at=task_link.created_at,
    )


# --------------------------------------------------------------------------- #
# GET /organizations/{org_id}/tasks/{task_id}/links — list task links         #
# --------------------------------------------------------------------------- #


@router.get("/tasks/{task_id}/links", response_model=list[TaskLinkOut])
def list_task_links(
    org_member: OrgMember,
    task_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> list[TaskLinkOut]:
    """List all links for a task (both outbound and inbound)."""
    org, _membership = org_member
    task = _get_task_or_404(db, org.id, task_id)
    # Just return from _task_to_out which merges both directions
    return _task_to_out(task).links


# --------------------------------------------------------------------------- #
# DELETE /organizations/{org_id}/tasks/links/{link_id} — delete task link     #
# --------------------------------------------------------------------------- #


@router.delete("/tasks/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_link(
    org_member: OrgMember,
    link_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> None:
    """Delete a task link (MEMBER+ required)."""
    org, _membership = org_member
    task_link = db.get(TaskLink, link_id)
    if task_link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found.")

    # Verify the source task belongs to this org
    source = db.get(Task, task_link.source_task_id)
    if source is None or source.organization_id != org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found.")

    write_audit(
        db,
        organization_id=org.id,
        actor_user_id=_membership.user_id,
        action="task.link_deleted",
        resource_type="task",
        resource_id=str(task_link.source_task_id),
        metadata={"target_task_id": str(task_link.target_task_id), "link_type": task_link.link_type},
    )
    db.delete(task_link)
    db.commit()
