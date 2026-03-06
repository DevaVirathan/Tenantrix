"""Organization management endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, OrgAdmin, OrgMember, OrgOwner
from app.db.session import get_db
from app.routers.organizations.schemas.org_schemas import (
    InviteCreateRequest,
    InviteOut,
    MemberOut,
    MemberRoleUpdateRequest,
    OrgCreateRequest,
    OrgOut,
    OrgUpdateRequest,
)
from app.routers.organizations.services.org_service import (
    accept_invite,
    change_member_role,
    create_invite,
    create_organization,
    list_org_members,
    list_user_organizations,
    remove_member,
    update_organization,
)

router = APIRouter(prefix="/organizations", tags=["organizations"])


# --------------------------------------------------------------------------- #
# POST /organizations                                                          #
# --------------------------------------------------------------------------- #
@router.post("", response_model=OrgOut, status_code=status.HTTP_201_CREATED)
def create_org(
    body: OrgCreateRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),  # noqa: B008
) -> OrgOut:
    org = create_organization(db, name=body.name, slug=body.slug, description=body.description, user_id=current_user.id)
    return OrgOut.model_validate(org)


# --------------------------------------------------------------------------- #
# GET /organizations                                                           #
# --------------------------------------------------------------------------- #
@router.get("", response_model=list[OrgOut])
def list_orgs(
    current_user: CurrentUser,
    db: Session = Depends(get_db),  # noqa: B008
) -> list[OrgOut]:
    orgs = list_user_organizations(db, current_user.id)
    return [OrgOut.model_validate(o) for o in orgs]


# --------------------------------------------------------------------------- #
# GET /organizations/{org_id}                                                  #
# --------------------------------------------------------------------------- #
@router.get("/{org_id}", response_model=OrgOut)
def get_org(org_and_membership: OrgMember) -> OrgOut:
    org, _ = org_and_membership
    return OrgOut.model_validate(org)


# --------------------------------------------------------------------------- #
# PATCH /organizations/{org_id}                                               #
# --------------------------------------------------------------------------- #
@router.patch("/{org_id}", response_model=OrgOut)
def update_org(
    body: OrgUpdateRequest,
    org_and_membership: OrgOwner,
    db: Session = Depends(get_db),  # noqa: B008
) -> OrgOut:
    org, acting_membership = org_and_membership
    org = update_organization(db, org=org, actor_user_id=acting_membership.user_id, name=body.name, description=body.description)
    return OrgOut.model_validate(org)


# --------------------------------------------------------------------------- #
# GET /organizations/{org_id}/members                                          #
# --------------------------------------------------------------------------- #
@router.get("/{org_id}/members", response_model=list[MemberOut])
def list_members(
    org_and_membership: OrgMember,
    db: Session = Depends(get_db),  # noqa: B008
) -> list[MemberOut]:
    org, _ = org_and_membership
    rows = list_org_members(db, org.id)
    return [MemberOut(user_id=m.user_id, role=m.role, status=m.status, joined_at=m.created_at) for m in rows]


# --------------------------------------------------------------------------- #
# POST /organizations/{org_id}/invites                                        #
# --------------------------------------------------------------------------- #
@router.post("/{org_id}/invites", response_model=InviteOut, status_code=status.HTTP_201_CREATED)
def send_invite(
    body: InviteCreateRequest,
    org_and_membership: OrgAdmin,
    db: Session = Depends(get_db),  # noqa: B008
) -> InviteOut:
    org, acting_membership = org_and_membership
    invite = create_invite(db, org_id=org.id, email=body.email, role=body.role, actor_user_id=acting_membership.user_id)
    return InviteOut.model_validate(invite)


# --------------------------------------------------------------------------- #
# POST /organizations/invites/accept/{token}                                  #
# --------------------------------------------------------------------------- #
@router.post("/invites/accept/{token}", response_model=OrgOut)
def accept_org_invite(
    token: str = Path(...),
    current_user: CurrentUser = ...,
    db: Session = Depends(get_db),  # noqa: B008
) -> OrgOut:
    org = accept_invite(db, token=token, user_id=current_user.id, user_email=current_user.email)
    return OrgOut.model_validate(org)


# --------------------------------------------------------------------------- #
# PATCH /organizations/{org_id}/members/{user_id}/role                       #
# --------------------------------------------------------------------------- #
@router.patch("/{org_id}/members/{user_id}/role", response_model=MemberOut)
def change_role(
    user_id: uuid.UUID,
    body: MemberRoleUpdateRequest,
    org_and_membership: OrgAdmin,
    db: Session = Depends(get_db),  # noqa: B008
) -> MemberOut:
    org, acting_membership = org_and_membership
    target = change_member_role(db, org_id=org.id, target_user_id=user_id, new_role=body.role, acting_membership=acting_membership)
    return MemberOut(user_id=target.user_id, role=target.role, status=target.status, joined_at=target.created_at)


# --------------------------------------------------------------------------- #
# DELETE /organizations/{org_id}/members/{user_id}                           #
# --------------------------------------------------------------------------- #
@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member_endpoint(
    user_id: uuid.UUID,
    org_and_membership: OrgAdmin,
    db: Session = Depends(get_db),  # noqa: B008
) -> None:
    org, acting_membership = org_and_membership
    remove_member(db, org_id=org.id, target_user_id=user_id, acting_membership=acting_membership)
