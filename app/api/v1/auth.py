"""Auth endpoints — register, login, refresh, logout, me."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser
from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    refresh_token_expiry,
    verify_password,
)
from app.db.session import get_db
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import (
    AccessTokenOut,
    LoginRequest,
    LogoutRequest,
    MessageOut,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# Convenience alias
DB = Annotated[Session, Depends(get_db)]


# --------------------------------------------------------------------------- #
# POST /auth/register                                                         #
# --------------------------------------------------------------------------- #
@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(body: RegisterRequest, db: DB) -> User:
    # Check duplicate email (case-insensitive)
    existing = db.query(User).filter(User.email == body.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        is_active=True,
    )
    db.add(user)
    db.flush()  # get user.id without committing
    return user


# --------------------------------------------------------------------------- #
# POST /auth/login                                                            #
# --------------------------------------------------------------------------- #
@router.post(
    "/login",
    response_model=TokenPair,
    summary="Authenticate and receive access + refresh tokens",
)
def login(body: LoginRequest, db: DB) -> TokenPair:
    user = db.query(User).filter(User.email == body.email.lower()).first()

    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive.",
        )

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


# --------------------------------------------------------------------------- #
# POST /auth/refresh                                                          #
# --------------------------------------------------------------------------- #
@router.post(
    "/refresh",
    response_model=AccessTokenOut,
    summary="Rotate refresh token and get a new access token",
)
def refresh(body: RefreshRequest, db: DB) -> AccessTokenOut:
    token_hash = hash_refresh_token(body.refresh_token)

    stored = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash)
        .first()
    )

    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        )

    # Reuse detection — if already revoked, invalidate entire family
    if stored.revoked:
        db.query(RefreshToken).filter(
            RefreshToken.family_id == stored.family_id
        ).update({"revoked": True, "revoked_at": datetime.now(UTC)})
        db.commit()  # commit the family wipe BEFORE raising so it persists
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token reuse detected. All sessions invalidated.",
        )

    if stored.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired.",
        )

    user = db.get(User, stored.user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        )

    # Revoke current token
    stored.revoked = True
    stored.revoked_at = datetime.now(UTC)

    # Issue new token in the same family
    new_access = create_access_token(str(user.id))
    raw_refresh, new_hash = generate_refresh_token()

    new_token = RefreshToken(
        user_id=user.id,
        token_hash=new_hash,
        expires_at=refresh_token_expiry(),
        family_id=stored.family_id,  # keep same family
    )
    db.add(new_token)

    return AccessTokenOut(
        access_token=new_access,
        refresh_token=raw_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# --------------------------------------------------------------------------- #
# POST /auth/logout                                                           #
# --------------------------------------------------------------------------- #
@router.post(
    "/logout",
    response_model=MessageOut,
    summary="Revoke the given refresh token",
)
def logout(body: LogoutRequest, db: DB) -> MessageOut:
    token_hash = hash_refresh_token(body.refresh_token)

    stored = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash)
        .first()
    )

    if stored and not stored.revoked:
        stored.revoked = True
        stored.revoked_at = datetime.now(UTC)

    # Always return 200 — don't leak token existence
    return MessageOut(message="Logged out successfully.")


# --------------------------------------------------------------------------- #
# GET /auth/me                                                                #
# --------------------------------------------------------------------------- #
@router.get(
    "/me",
    response_model=UserOut,
    summary="Return the currently authenticated user",
)
def me(current_user: CurrentUser) -> User:
    return current_user
