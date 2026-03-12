"""Saved Views endpoints — custom filtered views for projects."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import OrgAdmin, OrgMember
from app.db.session import get_db
from app.models.project import Project
from app.models.saved_view import SavedView
from app.schemas.saved_view import SavedViewCreate, SavedViewOut, SavedViewUpdate
from app.services.audit import write_audit

router = APIRouter(prefix="/organizations/{org_id}", tags=["saved-views"])


# --------------------------------------------------------------------------- #
# Helpers                                                                       #
# --------------------------------------------------------------------------- #


def _get_project_or_404(db: Session, org_id: uuid.UUID, project_id: uuid.UUID) -> Project:
    project = db.get(Project, project_id)
    if project is None or project.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return project


# --------------------------------------------------------------------------- #
# GET /organizations/{org_id}/projects/{project_id}/views — list               #
# --------------------------------------------------------------------------- #


@router.get("/projects/{project_id}/views", response_model=list[SavedViewOut])
def list_saved_views(
    org_member: OrgMember,
    project_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> list[SavedViewOut]:
    """List saved views: the current user's own views + shared views (MEMBER+ required)."""
    org, _membership = org_member
    _get_project_or_404(db, org.id, project_id)

    views = db.scalars(
        select(SavedView)
        .where(
            SavedView.project_id == project_id,
            SavedView.organization_id == org.id,
            or_(
                SavedView.created_by_user_id == _membership.user_id,
                SavedView.is_shared.is_(True),
            ),
        )
        .order_by(SavedView.created_at)
    ).all()
    return [SavedViewOut.model_validate(v) for v in views]


# --------------------------------------------------------------------------- #
# POST /organizations/{org_id}/projects/{project_id}/views — create            #
# --------------------------------------------------------------------------- #


@router.post(
    "/projects/{project_id}/views",
    response_model=SavedViewOut,
    status_code=status.HTTP_201_CREATED,
)
def create_saved_view(
    body: SavedViewCreate,
    org_member: OrgMember,
    project_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> SavedViewOut:
    """Create a new saved view in the project (MEMBER+ required)."""
    org, _membership = org_member
    _get_project_or_404(db, org.id, project_id)

    view = SavedView(
        project_id=project_id,
        organization_id=org.id,
        created_by_user_id=_membership.user_id,
        name=body.name,
        description=body.description,
        filters=body.filters,
        view_type=body.view_type,
        is_shared=body.is_shared,
    )
    db.add(view)
    db.flush()
    write_audit(
        db,
        organization_id=org.id,
        actor_user_id=_membership.user_id,
        action="saved_view.created",
        resource_type="saved_view",
        resource_id=str(view.id),
        metadata={"name": view.name, "project_id": str(project_id)},
    )
    db.commit()
    db.refresh(view)
    return SavedViewOut.model_validate(view)


# --------------------------------------------------------------------------- #
# PATCH /organizations/{org_id}/views/{view_id} — update (creator only)        #
# --------------------------------------------------------------------------- #


@router.patch("/views/{view_id}", response_model=SavedViewOut)
def update_saved_view(
    body: SavedViewUpdate,
    org_member: OrgMember,
    view_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> SavedViewOut:
    """Update a saved view (only the creator can update)."""
    org, _membership = org_member

    view = db.get(SavedView, view_id)
    if view is None or view.organization_id != org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved view not found.")

    if view.created_by_user_id != _membership.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the creator can update this view.",
        )

    if body.name is not None:
        view.name = body.name
    if "description" in body.model_fields_set:
        view.description = body.description
    if body.filters is not None:
        view.filters = body.filters
    if body.view_type is not None:
        view.view_type = body.view_type
    if body.is_shared is not None:
        view.is_shared = body.is_shared

    write_audit(
        db,
        organization_id=org.id,
        actor_user_id=_membership.user_id,
        action="saved_view.updated",
        resource_type="saved_view",
        resource_id=str(view.id),
        metadata={"name": view.name},
    )
    db.commit()
    db.refresh(view)
    return SavedViewOut.model_validate(view)


# --------------------------------------------------------------------------- #
# DELETE /organizations/{org_id}/views/{view_id} — delete (creator or admin)   #
# --------------------------------------------------------------------------- #


@router.delete("/views/{view_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_view(
    org_member: OrgMember,
    view_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> None:
    """Delete a saved view (creator or ADMIN+ required)."""
    org, _membership = org_member

    view = db.get(SavedView, view_id)
    if view is None or view.organization_id != org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved view not found.")

    # Allow deletion by creator or admin+
    is_creator = view.created_by_user_id == _membership.user_id
    is_admin = _membership.role in ("admin", "owner")
    if not is_creator and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the creator or an admin can delete this view.",
        )

    write_audit(
        db,
        organization_id=org.id,
        actor_user_id=_membership.user_id,
        action="saved_view.deleted",
        resource_type="saved_view",
        resource_id=str(view_id),
        metadata={"name": view.name},
    )
    db.delete(view)
    db.commit()
