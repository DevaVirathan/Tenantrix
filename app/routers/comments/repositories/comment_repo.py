"""Comments repository — DB queries for the comments domain."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.comment import Comment
from app.db.models.task import Task


def get_task_or_none(db: Session, org_id: uuid.UUID, task_id: uuid.UUID) -> Task | None:
    return db.scalars(select(Task).where(Task.id == task_id, Task.organization_id == org_id, Task.deleted_at.is_(None))).first()


def get_comment_or_none(db: Session, org_id: uuid.UUID, comment_id: uuid.UUID) -> Comment | None:
    return db.scalars(select(Comment).where(Comment.id == comment_id, Comment.organization_id == org_id, Comment.deleted_at.is_(None))).first()


def list_task_comments(db: Session, org_id: uuid.UUID, task_id: uuid.UUID) -> list[Comment]:
    return list(db.scalars(select(Comment).where(Comment.task_id == task_id, Comment.organization_id == org_id, Comment.deleted_at.is_(None)).order_by(Comment.created_at)).all())
