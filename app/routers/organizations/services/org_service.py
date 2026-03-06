"""Organizations service — business logic for the organizations domain."""

from __future__ import annotations

import re
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models.invite import Invite
from app.db.models.membership import Membership, MembershipStatus, OrgRole
from app.db.models.organization import Organization
from app.routers.organizations.repositories.org_repo import (
    get_active_members,
    get_active_memberships_for_user,
    get_invite_by_token,
    get_membership,
    get_open_invite_for_org_email,
    get_org_by_id,
    get_org_by_slug,
    get_orgs_by_ids,
    get_user_by_email,
)
from app.services.audit import write_audit

_INVITE_TTL_HOURS = 72


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9-]", "-", name.lower())[:100].strip("-")


def create_organization(db: Session, *, name: str, slug: str, description: str | None, user_id: uuid.UUID) -> Organization:
    if get_org_by_slug(db, slug) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already taken.")
    org = Organization(name=name, slug=slug, description=description, created_by_user_id=user_id)
    db.add(org)
    db.flush()
    membership = Membership(organization_id=org.id, user_id=user_id, role=OrgRole.OWNER, status=MembershipStatus.ACTIVE)
    db.add(membership)
    write_audit(db, organization_id=org.id, actor_user_id=user_id, action="org.created", resource_type="organization", resource_id=str(org.id), metadata={"name": org.name, "slug": org.slug})
    db.commit()
    db.refresh(org)
    return org


def list_user_organizations(db: Session, user_id: uuid.UUID) -> list[Organization]:
    memberships = get_active_memberships_for_user(db, user_id)
    org_ids = [m.organization_id for m in memberships]
    if not org_ids:
        return []
    return get_orgs_by_ids(db, org_ids)


def update_organization(db: Session, *, org: Organization, actor_user_id: uuid.UUID, name: str | None, description: str | None) -> Organization:
    if name is not None:
        org.name = name
    if description is not None:
        org.description = description
    write_audit(db, organization_id=org.id, actor_user_id=actor_user_id, action="org.updated", resource_type="organization", resource_id=str(org.id), metadata={"name": org.name})
    db.commit()
    db.refresh(org)
    return org


def list_org_members(db: Session, org_id: uuid.UUID) -> list[Membership]:
    return get_active_members(db, org_id)


def create_invite(db: Session, *, org_id: uuid.UUID, email: str, role: OrgRole, actor_user_id: uuid.UUID) -> Invite:
    target_user = get_user_by_email(db, email)
    if target_user is not None:
        existing = get_membership(db, org_id, target_user.id)
        if existing is not None and existing.status == MembershipStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a member of this organisation.")
    old_invite = get_open_invite_for_org_email(db, org_id, email)
    if old_invite is not None:
        db.delete(old_invite)
        db.flush()
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(hours=_INVITE_TTL_HOURS)
    invite = Invite(organization_id=org_id, email=email, token=token, role=role, expires_at=expires_at)
    db.add(invite)
    write_audit(db, organization_id=org_id, actor_user_id=actor_user_id, action="invite.sent", resource_type="invite", resource_id=str(invite.id), metadata={"email": email, "role": role})
    db.commit()
    db.refresh(invite)
    return invite


def accept_invite(db: Session, *, token: str, user_id: uuid.UUID, user_email: str) -> Organization:
    invite = get_invite_by_token(db, token)
    if invite is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found.")
    if invite.accepted_at is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invite already used.")
    if invite.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invite has expired.")
    if user_email.lower() != invite.email.lower():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This invite was sent to a different email address.")
    existing = get_membership(db, invite.organization_id, user_id)
    if existing is not None and existing.status == MembershipStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already a member of this organisation.")
    if existing is None:
        membership = Membership(organization_id=invite.organization_id, user_id=user_id, role=invite.role, status=MembershipStatus.ACTIVE)
        db.add(membership)
    else:
        existing.role = invite.role
        existing.status = MembershipStatus.ACTIVE
    invite.accepted_at = datetime.now(UTC)
    write_audit(db, organization_id=invite.organization_id, actor_user_id=user_id, action="invite.accepted", resource_type="membership", resource_id=str(user_id), metadata={"role": invite.role})
    db.commit()
    org = get_org_by_id(db, invite.organization_id)
    return org


def change_member_role(db: Session, *, org_id: uuid.UUID, target_user_id: uuid.UUID, new_role: OrgRole, acting_membership: Membership) -> Membership:
    if target_user_id == acting_membership.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change your own role.")
    target = get_membership(db, org_id, target_user_id)
    if target is None or target.status != MembershipStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")
    if target.role == OrgRole.OWNER and acting_membership.role != OrgRole.OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only an OWNER can change another OWNER'''s role.")
    if new_role == OrgRole.OWNER and acting_membership.role != OrgRole.OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only an OWNER can grant the OWNER role.")
    target.role = new_role
    write_audit(db, organization_id=org_id, actor_user_id=acting_membership.user_id, action="member.role_changed", resource_type="membership", resource_id=str(target_user_id), metadata={"new_role": str(new_role)})
    db.commit()
    db.refresh(target)
    return target


def remove_member(db: Session, *, org_id: uuid.UUID, target_user_id: uuid.UUID, acting_membership: Membership) -> None:
    if target_user_id == acting_membership.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove yourself. Transfer ownership first.")
    target = get_membership(db, org_id, target_user_id)
    if target is None or target.status != MembershipStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")
    if target.role == OrgRole.OWNER and acting_membership.role != OrgRole.OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only an OWNER can remove another OWNER.")
    db.delete(target)
    write_audit(db, organization_id=org_id, actor_user_id=acting_membership.user_id, action="member.removed", resource_type="membership", resource_id=str(target_user_id))
    db.commit()
