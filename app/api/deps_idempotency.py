"""Idempotency dependency — opt-in per endpoint via Depends()."""

from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.idempotency import get_cached_response, store_idempotency_response

_HEADER = "Idempotency-Key"


class IdempotencyResult:
    """Wrapper returned by the dependency."""

    def __init__(
        self,
        *,
        key: str | None,
        cached_status: int | None = None,
        cached_body: dict | None = None,
        org_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
        db: Session | None = None,
        method: str = "",
        path: str = "",
    ):
        self.key = key
        self.cached_status = cached_status
        self.cached_body = cached_body
        self._org_id = org_id
        self._user_id = user_id
        self._db = db
        self._method = method
        self._path = path

    @property
    def is_replay(self) -> bool:
        return self.cached_body is not None

    def store(self, response_status: int, response_body: dict) -> None:
        """Persist the response for future deduplication."""
        if self.key and self._db and self._org_id and self._user_id:
            store_idempotency_response(
                self._db,
                organization_id=self._org_id,
                user_id=self._user_id,
                key=self.key,
                method=self._method,
                path=self._path,
                response_status=response_status,
                response_body=response_body,
            )


def check_idempotency(
    request: Request,
    db: Session = Depends(get_db),  # noqa: B008
    current_user: User = Depends(get_current_user),  # noqa: B008
) -> IdempotencyResult:
    """
    Dependency that checks for an ``Idempotency-Key`` header.

    If the header is absent the request proceeds normally.
    If present and a cached response exists, returns it as a replay.
    """
    key = request.headers.get(_HEADER)
    if not key:
        return IdempotencyResult(key=None)

    # Extract org_id from path params
    org_id_str = request.path_params.get("org_id")
    if not org_id_str:
        return IdempotencyResult(key=None)

    org_id = uuid.UUID(org_id_str)
    method = request.method
    path = request.url.path

    cached = get_cached_response(
        db,
        organization_id=org_id,
        user_id=current_user.id,
        key=key,
        method=method,
        path=path,
    )

    if cached and cached.response_body is not None:
        return IdempotencyResult(
            key=key,
            cached_status=cached.response_status,
            cached_body=cached.response_body,
        )

    return IdempotencyResult(
        key=key,
        org_id=org_id,
        user_id=current_user.id,
        db=db,
        method=method,
        path=path,
    )
