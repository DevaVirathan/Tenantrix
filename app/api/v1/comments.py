"""Comment endpoints — M6."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import OrgMember
from app.db.session import get_db
from app.models.comment import Comment
from app.models.task import Task
from app.schemas.comment import CommentCreateRequest, CommentOut, CommentUpdateRequest
from app.models.user import User
from app.services.audit import write_audit
from app.services.notification import create_notification

router = APIRouter(prefix="/organizations/{org_id}", tags=["comments"])


# --------------------------------------------------------------------------- #
# Helpers                                                                       #
# --------------------------------------------------------------------------- #


def _get_task_or_404(db: Session, org_id: uuid.UUID, task_id: uuid.UUID) -> Task:
    task = db.scalars(
        select(Task).where(
            Task.id == task_id,
            Task.organization_id == org_id,
            Task.deleted_at.is_(None),
        )
    ).first()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    return task


def _get_comment_or_404(db: Session, org_id: uuid.UUID, comment_id: uuid.UUID) -> Comment:
    comment = db.scalars(
        select(Comment).where(
            Comment.id == comment_id,
            Comment.organization_id == org_id,
            Comment.deleted_at.is_(None),
        )
    ).first()
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found.")
    return comment


# --------------------------------------------------------------------------- #
# POST /organizations/{org_id}/tasks/{task_id}/comments — create               #
# --------------------------------------------------------------------------- #


@router.post(
    "/tasks/{task_id}/comments",
    response_model=CommentOut,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    body: CommentCreateRequest,
    org_member: OrgMember,
    task_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> CommentOut:
    """Add a comment to a task (MEMBER+ required)."""
    org, membership = org_member
    _get_task_or_404(db, org.id, task_id)

    comment = Comment(
        organization_id=org.id,
        task_id=task_id,
        author_user_id=membership.user_id,
        body=body.body,
    )
    db.add(comment)
    db.flush()
    write_audit(
        db,
        organization_id=org.id,
        actor_user_id=membership.user_id,
        action="comment.created",
        resource_type="comment",
        resource_id=str(comment.id),
        metadata={"task_id": str(task_id)},
    )
    # Notify task assignee and creator about new comment
    actor_user = db.get(User, membership.user_id)
    actor_name = (actor_user.full_name or actor_user.email) if actor_user else "Someone"
    task = _get_task_or_404(db, org.id, task_id)
    recipients: set[uuid.UUID] = set()
    if task.assignee_user_id:
        recipients.add(task.assignee_user_id)
    if task.created_by_user_id:
        recipients.add(task.created_by_user_id)
    for recipient_id in recipients:
        create_notification(
            db,
            recipient_user_id=recipient_id,
            actor_user_id=membership.user_id,
            organization_id=org.id,
            action_type="comment.created",
            resource_type="task",
            resource_id=str(task_id),
            message=f"{actor_name} commented on \"{task.title}\"",
        )

    db.commit()
    db.refresh(comment)
    return CommentOut.model_validate(comment)


# --------------------------------------------------------------------------- #
# GET /organizations/{org_id}/tasks/{task_id}/comments — list                  #
# --------------------------------------------------------------------------- #


@router.get("/tasks/{task_id}/comments", response_model=list[CommentOut])
def list_comments(
    org_member: OrgMember,
    task_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
    limit: int = Query(100, ge=1, le=500),  # noqa: B008
    offset: int = Query(0, ge=0),  # noqa: B008
) -> list[CommentOut]:
    """List all active comments on a task, oldest first (MEMBER+ required)."""
    org, _membership = org_member
    _get_task_or_404(db, org.id, task_id)

    comments = db.scalars(
        select(Comment)
        .where(
            Comment.task_id == task_id,
            Comment.organization_id == org.id,
            Comment.deleted_at.is_(None),
        )
        .order_by(Comment.created_at)
        .limit(limit)
        .offset(offset)
    ).all()
    return [CommentOut.model_validate(c) for c in comments]


# --------------------------------------------------------------------------- #
# PATCH /organizations/{org_id}/comments/{comment_id} — update                 #
# --------------------------------------------------------------------------- #


@router.patch("/comments/{comment_id}", response_model=CommentOut)
def update_comment(
    body: CommentUpdateRequest,
    org_member: OrgMember,
    comment_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> CommentOut:
    """Edit a comment body — author or ADMIN+ only (MEMBER+ required to reach endpoint)."""
    org, membership = org_member
    comment = _get_comment_or_404(db, org.id, comment_id)

    # Only the author or an admin/owner may edit
    is_author = comment.author_user_id == membership.user_id
    is_admin_plus = membership.role in ("admin", "owner")
    if not is_author and not is_admin_plus:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the comment author or an admin can edit this comment.",
        )

    comment.body = body.body
    write_audit(
        db,
        organization_id=org.id,
        actor_user_id=membership.user_id,
        action="comment.updated",
        resource_type="comment",
        resource_id=str(comment_id),
    )
    db.commit()
    db.refresh(comment)
    return CommentOut.model_validate(comment)


# --------------------------------------------------------------------------- #
# DELETE /organizations/{org_id}/comments/{comment_id} — soft delete           #
# --------------------------------------------------------------------------- #


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    org_member: OrgMember,
    comment_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> None:
    """Soft-delete a comment — author or ADMIN+ only."""
    org, membership = org_member
    comment = _get_comment_or_404(db, org.id, comment_id)

    is_author = comment.author_user_id == membership.user_id
    is_admin_plus = membership.role in ("admin", "owner")
    if not is_author and not is_admin_plus:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the comment author or an admin can delete this comment.",
        )

    comment.deleted_at = datetime.now(UTC)
    write_audit(
        db,
        organization_id=org.id,
        actor_user_id=membership.user_id,
        action="comment.deleted",
        resource_type="comment",
        resource_id=str(comment_id),
    )
    db.commit()
