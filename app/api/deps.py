"""FastAPI dependencies — reusable across all API routes."""

from __future__ import annotations

import uuid
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Path, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.models.membership import Membership, OrgRole
from app.db.models.organization import Organization
from app.db.models.user import User
from app.db.session import get_db

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Extract + verify the Bearer JWT and return the active User.

    Raises HTTP 401 on any auth failure.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except jwt.PyJWTError as exc:
        raise credentials_exception from exc

    user_id: str | None = payload.get("sub")
    token_type: str | None = payload.get("type")

    if user_id is None or token_type != "access":
        raise credentials_exception

    user = db.get(User, user_id)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive.",
        )
    return user


# Convenience type alias used in route signatures
CurrentUser = Annotated[User, Depends(get_current_user)]


# --------------------------------------------------------------------------- #
# Organisation RBAC dependency                                                  #
# --------------------------------------------------------------------------- #

_ROLE_RANK: dict[OrgRole, int] = {
    OrgRole.VIEWER: 0,
    OrgRole.MEMBER: 1,
    OrgRole.ADMIN: 2,
    OrgRole.OWNER: 3,
}


def require_org_role(minimum_role: OrgRole = OrgRole.MEMBER):
    """
    Return a FastAPI dependency that:
      1. Resolves the organisation from the path param ``org_id``.
      2. Verifies the current user has an ACTIVE membership with at least
         ``minimum_role``.
      3. Returns the ``(org, membership)`` tuple so routes can use it.
    """

    def _dep(
        org_id: uuid.UUID = Path(...),  # noqa: B008
        current_user: User = Depends(get_current_user),  # noqa: B008
        db: Session = Depends(get_db),  # noqa: B008
    ) -> tuple[Organization, Membership]:
        org = db.get(Organization, org_id)
        if org is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Organisation not found."
            )

        membership = (
            db.query(Membership).filter_by(organization_id=org_id, user_id=current_user.id).first()
        )
        if membership is None or membership.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this organisation."
            )

        if _ROLE_RANK[membership.role] < _ROLE_RANK[minimum_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires at least {minimum_role} role.",
            )
        return org, membership

    return _dep


# Type aliases for common role checks
OrgMember = Annotated[tuple[Organization, Membership], Depends(require_org_role(OrgRole.MEMBER))]
OrgAdmin = Annotated[tuple[Organization, Membership], Depends(require_org_role(OrgRole.ADMIN))]
OrgOwner = Annotated[tuple[Organization, Membership], Depends(require_org_role(OrgRole.OWNER))]
