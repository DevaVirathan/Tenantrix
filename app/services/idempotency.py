"""Idempotency key service — deduplicate mutating POST requests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.idempotency_key import IdempotencyKey

_TTL_HOURS = 24


def get_cached_response(
    db: Session,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    key: str,
    method: str,
    path: str,
) -> IdempotencyKey | None:
    """
    Look up an existing idempotency record.

    Returns the record if found (caller should replay it) or None if this is a fresh request.
    Raises HTTP 409 if the same key was used on a different method/path (key collision).
    """
    record = (
        db.query(IdempotencyKey)
        .filter_by(organization_id=organization_id, user_id=user_id, key=key)
        .first()
    )
    if record is None:
        return None

    # Key reused on a different endpoint — reject
    if record.request_method != method or record.request_path != path:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Idempotency key '{key}' was already used for "
                f"{record.request_method} {record.request_path}."
            ),
        )

    # Expired record — treat as new
    if record.expires_at and record.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        db.delete(record)
        db.flush()
        return None

    return record


def store_idempotency_response(
    db: Session,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    key: str,
    method: str,
    path: str,
    response_status: int,
    response_body: dict,
) -> IdempotencyKey:
    """Persist a completed response so future duplicate requests get the same reply."""
    expires_at = datetime.now(UTC) + timedelta(hours=_TTL_HOURS)
    record = IdempotencyKey(
        organization_id=organization_id,
        user_id=user_id,
        key=key,
        request_method=method,
        request_path=path,
        response_status=response_status,
        response_body=response_body,
        expires_at=expires_at,
    )
    db.add(record)
    db.flush()
    return record
