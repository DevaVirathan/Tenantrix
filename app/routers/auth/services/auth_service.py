"""Auth service — business logic for auth domain."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    refresh_token_expiry,
    verify_password,
)
from app.db.models.refresh_token import RefreshToken
from app.db.models.user import User
from app.routers.auth.repositories.auth_repo import (
    get_refresh_token_by_hash,
    get_refresh_tokens_by_family,
    get_user_by_email,
    get_user_by_id,
)
from app.routers.auth.schemas.auth_schemas import (
    AccessTokenOut,
    TokenPair,
)


def create_user(db: Session, email: str, password: str, full_name: str | None) -> User:
    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        full_name=full_name,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


def issue_token_pair(db: Session, user: User) -> TokenPair:
    access_token = create_access_token(str(user.id))
    raw_refresh, refresh_hash = generate_refresh_token()
    token = RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=refresh_token_expiry(),
        family_id=uuid.uuid4(),
    )
    db.add(token)
    return TokenPair(
        access_token=access_token,
        refresh_token=raw_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def rotate_refresh_token(db: Session, refresh_token_str: str) -> AccessTokenOut:
    from fastapi import HTTPException, status
    token_hash = hash_refresh_token(refresh_token_str)
    stored = get_refresh_token_by_hash(db, token_hash)
    if stored is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")
    if stored.revoked:
        for t in get_refresh_tokens_by_family(db, stored.family_id):
            t.revoked = True
            t.revoked_at = datetime.now(UTC)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token reuse detected. All sessions invalidated.",
        )
    if stored.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has expired.")
    user = get_user_by_id(db, stored.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")
    stored.revoked = True
    stored.revoked_at = datetime.now(UTC)
    new_access = create_access_token(str(user.id))
    raw_refresh, new_hash = generate_refresh_token()
    new_token = RefreshToken(
        user_id=user.id,
        token_hash=new_hash,
        expires_at=refresh_token_expiry(),
        family_id=stored.family_id,
    )
    db.add(new_token)
    return AccessTokenOut(
        access_token=new_access,
        refresh_token=raw_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def revoke_refresh_token(db: Session, refresh_token_str: str) -> None:
    token_hash = hash_refresh_token(refresh_token_str)
    stored = get_refresh_token_by_hash(db, token_hash)
    if stored and not stored.revoked:
        stored.revoked = True
        stored.revoked_at = datetime.now(UTC)
