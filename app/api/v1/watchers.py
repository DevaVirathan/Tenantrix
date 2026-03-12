"""Task watcher endpoints — watch/unwatch tasks for notifications."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, OrgMember
from app.db.session import get_db
from app.models.task import Task
from app.models.task_watcher import TaskWatcher
from app.models.user import User

router = APIRouter(prefix="/organizations/{org_id}", tags=["watchers"])


@router.get("/tasks/{task_id}/watchers")
def list_watchers(
    org_member: OrgMember,
    task_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> list[dict]:
    """List all watchers for a task."""
    org, _ = org_member
    task = db.scalar(
        select(Task).where(Task.id == task_id, Task.organization_id == org.id, Task.deleted_at.is_(None))
    )
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")

    rows = db.execute(
        select(TaskWatcher.user_id, User.full_name, User.email)
        .join(User, User.id == TaskWatcher.user_id)
        .where(TaskWatcher.task_id == task_id)
    ).all()

    return [
        {"user_id": str(r[0]), "full_name": r[1], "email": r[2]}
        for r in rows
    ]


@router.post("/tasks/{task_id}/watchers", status_code=status.HTTP_201_CREATED)
def add_watcher(
    org_member: OrgMember,
    current_user: CurrentUser,
    task_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> dict:
    """Add current user as a watcher of the task."""
    org, _ = org_member
    task = db.scalar(
        select(Task).where(Task.id == task_id, Task.organization_id == org.id, Task.deleted_at.is_(None))
    )
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")

    existing = db.scalar(
        select(TaskWatcher).where(TaskWatcher.task_id == task_id, TaskWatcher.user_id == current_user.id)
    )
    if existing:
        return {"detail": "Already watching."}

    watcher = TaskWatcher(task_id=task_id, user_id=current_user.id)
    db.add(watcher)
    db.commit()
    return {"detail": "Watching."}


@router.delete("/tasks/{task_id}/watchers", status_code=status.HTTP_204_NO_CONTENT)
def remove_watcher(
    org_member: OrgMember,
    current_user: CurrentUser,
    task_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> None:
    """Remove current user from watchers of the task."""
    org, _ = org_member
    watcher = db.scalar(
        select(TaskWatcher).where(TaskWatcher.task_id == task_id, TaskWatcher.user_id == current_user.id)
    )
    if watcher:
        db.delete(watcher)
        db.commit()
