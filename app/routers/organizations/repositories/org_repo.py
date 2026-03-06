"""Organizations repository — DB queries for the organizations domain."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.invite import Invite
from app.db.models.membership import Membership, MembershipStatus
from app.db.models.organization import Organization
from app.db.models.user import User


def get_org_by_slug(db: Session, slug: str) -> Organization | None:
    return db.scalar(select(Organization).where(Organization.slug == slug))


def get_org_by_id(db: Session, org_id: uuid.UUID) -> Organization | None:
    return db.get(Organization, org_id)


def get_active_memberships_for_user(db: Session, user_id: uuid.UUID) -> list[Membership]:
    return db.query(Membership).filter_by(user_id=user_id, status=MembershipStatus.ACTIVE).all()


def get_orgs_by_ids(db: Session, org_ids: list[uuid.UUID]) -> list[Organization]:
    return list(
        db.scalars(
            select(Organization)
            .where(Organization.id.in_(org_ids))
            .order_by(Organization.created_at.desc())
        ).all()
    )


def get_active_members(db: Session, org_id: uuid.UUID) -> list[Membership]:
    return db.query(Membership).filter_by(organization_id=org_id, status=MembershipStatus.ACTIVE).all()


def get_membership(db: Session, org_id: uuid.UUID, user_id: uuid.UUID) -> Membership | None:
    return db.query(Membership).filter_by(organization_id=org_id, user_id=user_id).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def get_open_invite_for_org_email(db: Session, org_id: uuid.UUID, email: str) -> Invite | None:
    return db.scalar(
        select(Invite).where(
            Invite.organization_id == org_id,
            Invite.email == email,
            Invite.accepted_at.is_(None),
        )
    )


def get_invite_by_token(db: Session, token: str) -> Invite | None:
    return db.scalar(select(Invite).where(Invite.token == token))
