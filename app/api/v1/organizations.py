"""Organization management endpoints — M3."""

from __future__ import annotations

import re
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, OrgAdmin, OrgMember
from app.db.session import get_db
from app.models.invite import Invite
from app.models.membership import Membership, MembershipStatus, OrgRole
from app.models.organization import Organization
from app.models.user import User
from app.schemas.organization import (
    InviteCreateRequest,
    InviteOut,
    MemberOut,
    MemberRoleUpdateRequest,
    OrgCreateRequest,
    OrgOut,
)

router = APIRouter(prefix="/organizations", tags=["organizations"])

_INVITE_TTL_HOURS = 72


# --------------------------------------------------------------------------- #
# Helpers                                                                       #
# --------------------------------------------------------------------------- #


def _slugify(name: str) -> str:
    """Naïve slug from name — callers should supply an explicit slug instead."""
    return re.sub(r"[^a-z0-9-]", "-", name.lower())[:100].strip("-")


# --------------------------------------------------------------------------- #
# POST /organizations — create a new org                                        #
# --------------------------------------------------------------------------- #


@router.post("", response_model=OrgOut, status_code=status.HTTP_201_CREATED)
def create_organization(
    body: OrgCreateRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),  # noqa: B008
) -> OrgOut:
    # Check slug uniqueness
    existing = db.scalar(select(Organization).where(Organization.slug == body.slug))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Slug already taken.",
        )

    org = Organization(
        name=body.name,
        slug=body.slug,
        description=body.description,
        created_by_user_id=current_user.id,
    )
    db.add(org)
    db.flush()  # get org.id before membership insert

    membership = Membership(
        organization_id=org.id,
        user_id=current_user.id,
        role=OrgRole.OWNER,
        status=MembershipStatus.ACTIVE,
    )
    db.add(membership)
    db.commit()
    db.refresh(org)
    return OrgOut.model_validate(org)


# --------------------------------------------------------------------------- #
# GET /organizations/{org_id} — fetch org detail                               #
# --------------------------------------------------------------------------- #


@router.get("/{org_id}", response_model=OrgOut)
def get_organization(
    org_and_membership: OrgMember,
) -> OrgOut:
    org, _ = org_and_membership
    return OrgOut.model_validate(org)


# --------------------------------------------------------------------------- #
# GET /organizations/{org_id}/members — list active members                    #
# --------------------------------------------------------------------------- #


@router.get("/{org_id}/members", response_model=list[MemberOut])
def list_members(
    org_and_membership: OrgMember,
    db: Session = Depends(get_db),  # noqa: B008
) -> list[MemberOut]:
    org, _ = org_and_membership
    rows = (
        db.query(Membership).filter_by(organization_id=org.id, status=MembershipStatus.ACTIVE).all()
    )
    return [
        MemberOut(
            user_id=m.user_id,
            role=m.role,
            status=m.status,
            joined_at=m.created_at,
        )
        for m in rows
    ]


# --------------------------------------------------------------------------- #
# POST /organizations/{org_id}/invites — send invite                           #
# --------------------------------------------------------------------------- #


@router.post(
    "/{org_id}/invites",
    response_model=InviteOut,
    status_code=status.HTTP_201_CREATED,
)
def create_invite(
    body: InviteCreateRequest,
    org_and_membership: OrgAdmin,
    db: Session = Depends(get_db),  # noqa: B008
) -> InviteOut:
    org, _ = org_and_membership

    # Prevent inviting someone already a member
    target_user = db.scalar(select(User).where(User.email == body.email))
    if target_user is not None:
        existing_membership = (
            db.query(Membership).filter_by(organization_id=org.id, user_id=target_user.id).first()
        )
        if (
            existing_membership is not None
            and existing_membership.status == MembershipStatus.ACTIVE
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this organisation.",
            )

    # Invalidate any existing open invite for the same email+org
    old_invite = db.scalar(
        select(Invite).where(
            Invite.organization_id == org.id,
            Invite.email == body.email,
            Invite.accepted_at.is_(None),
        )
    )
    if old_invite is not None:
        db.delete(old_invite)
        db.flush()

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(hours=_INVITE_TTL_HOURS)
    invite = Invite(
        organization_id=org.id,
        email=body.email,
        token=token,
        role=body.role,
        expires_at=expires_at,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return InviteOut.model_validate(invite)


# --------------------------------------------------------------------------- #
# POST /organizations/invites/accept/{token} — accept invite                  #
# --------------------------------------------------------------------------- #


@router.post("/invites/accept/{token}", response_model=OrgOut)
def accept_invite(
    token: str = Path(...),
    current_user: CurrentUser = ...,  # type: ignore[assignment]
    db: Session = Depends(get_db),  # noqa: B008
) -> OrgOut:
    invite = db.scalar(select(Invite).where(Invite.token == token))

    if invite is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found.")

    if invite.accepted_at is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invite already used.")

    if invite.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invite has expired.")

    if current_user.email.lower() != invite.email.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invite was sent to a different email address.",
        )

    # Check for an existing membership
    existing = (
        db.query(Membership)
        .filter_by(organization_id=invite.organization_id, user_id=current_user.id)
        .first()
    )
    if existing is not None and existing.status == MembershipStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already a member of this organisation.",
        )

    if existing is None:
        membership = Membership(
            organization_id=invite.organization_id,
            user_id=current_user.id,
            role=invite.role,
            status=MembershipStatus.ACTIVE,
        )
        db.add(membership)
    else:
        # Reactivate a previously removed membership
        existing.role = invite.role
        existing.status = MembershipStatus.ACTIVE

    invite.accepted_at = datetime.now(UTC)
    db.commit()

    org = db.get(Organization, invite.organization_id)
    return OrgOut.model_validate(org)


# --------------------------------------------------------------------------- #
# PATCH /organizations/{org_id}/members/{user_id}/role — change role          #
# --------------------------------------------------------------------------- #


@router.patch("/{org_id}/members/{user_id}/role", response_model=MemberOut)
def change_member_role(
    user_id: uuid.UUID,
    body: MemberRoleUpdateRequest,
    org_and_membership: OrgAdmin,
    db: Session = Depends(get_db),  # noqa: B008
) -> MemberOut:
    org, acting_membership = org_and_membership

    if user_id == acting_membership.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role.",
        )

    target = db.query(Membership).filter_by(organization_id=org.id, user_id=user_id).first()
    if target is None or target.status != MembershipStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")

    # Only OWNERs may promote/demote other OWNERs
    if target.role == OrgRole.OWNER and acting_membership.role != OrgRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only an OWNER can change another OWNER's role.",
        )
    if body.role == OrgRole.OWNER and acting_membership.role != OrgRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only an OWNER can grant the OWNER role.",
        )

    target.role = body.role
    db.commit()
    db.refresh(target)
    return MemberOut(
        user_id=target.user_id,
        role=target.role,
        status=target.status,
        joined_at=target.created_at,
    )


# --------------------------------------------------------------------------- #
# DELETE /organizations/{org_id}/members/{user_id} — remove member            #
# --------------------------------------------------------------------------- #


@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    user_id: uuid.UUID,
    org_and_membership: OrgAdmin,
    db: Session = Depends(get_db),  # noqa: B008
) -> None:
    org, acting_membership = org_and_membership

    if user_id == acting_membership.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself. Transfer ownership first.",
        )

    target = db.query(Membership).filter_by(organization_id=org.id, user_id=user_id).first()
    if target is None or target.status != MembershipStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")

    if target.role == OrgRole.OWNER and acting_membership.role != OrgRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only an OWNER can remove another OWNER.",
        )

    db.delete(target)
    db.commit()
