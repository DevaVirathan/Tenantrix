"""Comment endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from app.api.deps import OrgMember
from app.db.session import get_db
from app.routers.comments.schemas.comment_schemas import (
    CommentCreateRequest,
    CommentOut,
    CommentUpdateRequest,
)
from app.routers.comments.services.comment_service import (
    create_comment,
    delete_comment,
    list_comments,
    update_comment,
)

router = APIRouter(prefix="/organizations/{org_id}", tags=["comments"])


@router.post("/tasks/{task_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def create_comment_endpoint(
    body: CommentCreateRequest,
    org_member: OrgMember,
    task_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    org, membership = org_member
    return create_comment(db, org_id=org.id, task_id=task_id, author_user_id=membership.user_id, body=body.body)


@router.get("/tasks/{task_id}/comments", response_model=list[CommentOut])
def list_comments_endpoint(
    org_member: OrgMember,
    task_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    org, _ = org_member
    return list_comments(db, org.id, task_id)


@router.patch("/comments/{comment_id}", response_model=CommentOut)
def update_comment_endpoint(
    body: CommentUpdateRequest,
    org_member: OrgMember,
    comment_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    org, membership = org_member
    return update_comment(db, org_id=org.id, comment_id=comment_id, membership=membership, body=body.body)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment_endpoint(
    org_member: OrgMember,
    comment_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
):
    org, membership = org_member
    delete_comment(db, org_id=org.id, comment_id=comment_id, membership=membership)
