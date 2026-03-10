"""Notification service — create in-app notifications."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.notification import Notification


def create_notification(
    db: Session,
    *,
    recipient_user_id: uuid.UUID,
    actor_user_id: uuid.UUID | None,
    organization_id: uuid.UUID,
    action_type: str,
    resource_type: str,
    resource_id: str,
    message: str,
) -> Notification:
    """Create an in-app notification for a user."""
    # Don't notify the actor about their own action
    if actor_user_id and recipient_user_id == actor_user_id:
        return None  # type: ignore[return-value]

    notification = Notification(
        recipient_user_id=recipient_user_id,
        actor_user_id=actor_user_id,
        organization_id=organization_id,
        action_type=action_type,
        resource_type=resource_type,
        resource_id=resource_id,
        message=message,
    )
    db.add(notification)
    return notification
