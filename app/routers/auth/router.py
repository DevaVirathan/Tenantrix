"""Auth endpoints — register, login, refresh, logout, me."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser
from app.core.limiter import limiter
from app.db.models.user import User
from app.db.session import get_db
from app.routers.auth.repositories.auth_repo import get_user_by_email
from app.routers.auth.schemas.auth_schemas import (
    AccessTokenOut,
    LoginRequest,
    LogoutRequest,
    MessageOut,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserOut,
)
from app.routers.auth.services.auth_service import (
    authenticate_user,
    create_user,
    issue_token_pair,
    revoke_refresh_token,
    rotate_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])

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
@limiter.limit("10/minute")
def register(request: Request, body: RegisterRequest, db: DB) -> User:
    existing = get_user_by_email(db, body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    return create_user(db, body.email, body.password, body.full_name)


# --------------------------------------------------------------------------- #
# POST /auth/login                                                            #
# --------------------------------------------------------------------------- #
@router.post(
    "/login",
    response_model=TokenPair,
    summary="Authenticate and receive access + refresh tokens",
)
@limiter.limit("10/minute")
def login(request: Request, body: LoginRequest, db: DB) -> TokenPair:
    user = authenticate_user(db, body.email, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive.",
        )
    return issue_token_pair(db, user)


# --------------------------------------------------------------------------- #
# POST /auth/refresh                                                          #
# --------------------------------------------------------------------------- #
@router.post(
    "/refresh",
    response_model=AccessTokenOut,
    summary="Rotate refresh token and get a new access token",
)
@limiter.limit("20/minute")
def refresh(request: Request, body: RefreshRequest, db: DB) -> AccessTokenOut:
    return rotate_refresh_token(db, body.refresh_token)


# --------------------------------------------------------------------------- #
# POST /auth/logout                                                           #
# --------------------------------------------------------------------------- #
@router.post(
    "/logout",
    response_model=MessageOut,
    summary="Revoke the given refresh token",
)
def logout(body: LogoutRequest, db: DB) -> MessageOut:
    revoke_refresh_token(db, body.refresh_token)
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
