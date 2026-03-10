"""Notification endpoints."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.models.notification import Notification
from app.schemas.notification import NotificationOut, UnreadCountOut

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
def list_notifications(
    current_user: CurrentUser,
    db: Session = Depends(get_db),  # noqa: B008
    org_id: uuid.UUID | None = Query(None),  # noqa: B008
    limit: int = Query(50, ge=1, le=100),  # noqa: B008
    offset: int = Query(0, ge=0),  # noqa: B008
) -> list[NotificationOut]:
    """List notifications for the current user."""
    q = (
        select(Notification)
        .where(Notification.recipient_user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if org_id is not None:
        q = q.where(Notification.organization_id == org_id)
    return [NotificationOut.model_validate(n) for n in db.scalars(q).all()]


@router.get("/unread-count", response_model=UnreadCountOut)
def unread_count(
    current_user: CurrentUser,
    db: Session = Depends(get_db),  # noqa: B008
) -> UnreadCountOut:
    """Get the count of unread notifications."""
    count = db.scalar(
        select(func.count(Notification.id)).where(
            Notification.recipient_user_id == current_user.id,
            Notification.read_at.is_(None),
        )
    )
    return UnreadCountOut(count=count or 0)


@router.patch("/{notification_id}/read", response_model=NotificationOut)
def mark_as_read(
    current_user: CurrentUser,
    notification_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> NotificationOut:
    """Mark a single notification as read."""
    notification = db.get(Notification, notification_id)
    if notification is None or notification.recipient_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    notification.read_at = datetime.now(UTC)
    db.commit()
    db.refresh(notification)
    return NotificationOut.model_validate(notification)


@router.post("/mark-all-read", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_read(
    current_user: CurrentUser,
    db: Session = Depends(get_db),  # noqa: B008
) -> None:
    """Mark all unread notifications as read."""
    from sqlalchemy import update
    db.execute(
        update(Notification)
        .where(
            Notification.recipient_user_id == current_user.id,
            Notification.read_at.is_(None),
        )
        .values(read_at=datetime.now(UTC))
    )
    db.commit()
