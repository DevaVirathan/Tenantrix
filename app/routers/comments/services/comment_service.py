"""Comments service — business logic for the comments domain."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.comment import Comment
from app.db.models.membership import Membership
from app.routers.comments.repositories.comment_repo import (
    get_comment_or_none,
    get_task_or_none,
    list_task_comments,
)
from app.services.audit import write_audit


def _get_task_or_404(db, org_id, task_id):
    task = get_task_or_none(db, org_id, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    return task


def _get_comment_or_404(db, org_id, comment_id):
    comment = get_comment_or_none(db, org_id, comment_id)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found.")
    return comment


def create_comment(db: Session, *, org_id: uuid.UUID, task_id: uuid.UUID, author_user_id: uuid.UUID, body: str) -> Comment:
    _get_task_or_404(db, org_id, task_id)
    comment = Comment(organization_id=org_id, task_id=task_id, author_user_id=author_user_id, body=body)
    db.add(comment)
    db.flush()
    write_audit(db, organization_id=org_id, actor_user_id=author_user_id, action="comment.created", resource_type="comment", resource_id=str(comment.id), metadata={"task_id": str(task_id)})
    db.commit()
    db.refresh(comment)
    return comment


def list_comments(db: Session, org_id: uuid.UUID, task_id: uuid.UUID) -> list[Comment]:
    _get_task_or_404(db, org_id, task_id)
    return list_task_comments(db, org_id, task_id)


def update_comment(db: Session, *, org_id: uuid.UUID, comment_id: uuid.UUID, membership: Membership, body: str) -> Comment:
    comment = _get_comment_or_404(db, org_id, comment_id)
    is_author = comment.author_user_id == membership.user_id
    is_admin_plus = membership.role in ("admin", "owner")
    if not is_author and not is_admin_plus:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the comment author or an admin can edit this comment.")
    comment.body = body
    write_audit(db, organization_id=org_id, actor_user_id=membership.user_id, action="comment.updated", resource_type="comment", resource_id=str(comment_id))
    db.commit()
    db.refresh(comment)
    return comment


def delete_comment(db: Session, *, org_id: uuid.UUID, comment_id: uuid.UUID, membership: Membership) -> None:
    comment = _get_comment_or_404(db, org_id, comment_id)
    is_author = comment.author_user_id == membership.user_id
    is_admin_plus = membership.role in ("admin", "owner")
    if not is_author and not is_admin_plus:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the comment author or an admin can delete this comment.")
    comment.deleted_at = datetime.now(UTC)
    write_audit(db, organization_id=org_id, actor_user_id=membership.user_id, action="comment.deleted", resource_type="comment", resource_id=str(comment_id))
    db.commit()
