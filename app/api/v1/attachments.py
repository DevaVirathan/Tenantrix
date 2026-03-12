"""Attachment endpoints — file upload/download/delete for tasks."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, UploadFile, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import OrgAdmin, OrgMember
from app.db.session import get_db
from app.models.attachment import Attachment
from app.models.task import Task
from app.schemas.attachment import AttachmentOut
from app.services.audit import write_audit
from app.services.storage import get_storage

router = APIRouter(prefix="/organizations/{org_id}", tags=["attachments"])


# --------------------------------------------------------------------------- #
# Helpers                                                                       #
# --------------------------------------------------------------------------- #


def _get_task_or_404(db: Session, org_id: uuid.UUID, task_id: uuid.UUID) -> Task:
    task = db.scalars(
        select(Task).where(
            Task.id == task_id,
            Task.organization_id == org_id,
            Task.deleted_at.is_(None),
        )
    ).first()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    return task


# --------------------------------------------------------------------------- #
# POST /organizations/{org_id}/tasks/{task_id}/attachments — upload            #
# --------------------------------------------------------------------------- #


@router.post(
    "/tasks/{task_id}/attachments",
    response_model=AttachmentOut,
    status_code=status.HTTP_201_CREATED,
)
def upload_attachment(
    org_member: OrgMember,
    file: UploadFile,
    task_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> AttachmentOut:
    """Upload a file attachment to a task (MEMBER+ required)."""
    org, membership = org_member
    task = _get_task_or_404(db, org.id, task_id)

    if file.filename is None or file.size is None or file.size == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File is empty or missing a filename.",
        )

    # Build a unique S3 key
    attachment_id = uuid.uuid4()
    s3_key = f"orgs/{org.id}/tasks/{task.id}/{attachment_id}/{file.filename}"

    # Upload to S3
    storage = get_storage()
    storage.upload_file(file.file, s3_key, content_type=file.content_type or "application/octet-stream")

    attachment = Attachment(
        id=attachment_id,
        task_id=task.id,
        organization_id=org.id,
        uploaded_by_user_id=membership.user_id,
        filename=file.filename,
        file_size=file.size,
        mime_type=file.content_type or "application/octet-stream",
        s3_key=s3_key,
    )
    db.add(attachment)
    write_audit(
        db,
        organization_id=org.id,
        actor_user_id=membership.user_id,
        action="attachment.uploaded",
        resource_type="attachment",
        resource_id=str(attachment.id),
        metadata={"filename": file.filename, "task_id": str(task.id)},
    )
    db.commit()
    db.refresh(attachment)
    return AttachmentOut.model_validate(attachment)


# --------------------------------------------------------------------------- #
# GET /organizations/{org_id}/tasks/{task_id}/attachments — list               #
# --------------------------------------------------------------------------- #


@router.get("/tasks/{task_id}/attachments", response_model=list[AttachmentOut])
def list_attachments(
    org_member: OrgMember,
    task_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> list[AttachmentOut]:
    """List all attachments for a task (MEMBER+ required)."""
    org, _membership = org_member
    _get_task_or_404(db, org.id, task_id)

    attachments = db.scalars(
        select(Attachment)
        .where(Attachment.task_id == task_id, Attachment.organization_id == org.id)
        .order_by(Attachment.created_at.desc())
    ).all()
    return [AttachmentOut.model_validate(a) for a in attachments]


# --------------------------------------------------------------------------- #
# GET /organizations/{org_id}/attachments/{attachment_id}/download — presigned #
# --------------------------------------------------------------------------- #


@router.get("/attachments/{attachment_id}/download")
def download_attachment(
    org_member: OrgMember,
    attachment_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> RedirectResponse:
    """Redirect to a presigned S3 URL for downloading the attachment (MEMBER+ required)."""
    org, _membership = org_member
    attachment = db.get(Attachment, attachment_id)
    if attachment is None or attachment.organization_id != org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")

    storage = get_storage()
    url = storage.get_presigned_url(attachment.s3_key)
    return RedirectResponse(url=url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


# --------------------------------------------------------------------------- #
# DELETE /organizations/{org_id}/attachments/{attachment_id} — delete          #
# --------------------------------------------------------------------------- #


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    org_member: OrgMember,
    attachment_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> None:
    """Delete an attachment. Only the uploader or an org admin can delete (MEMBER+ required)."""
    org, membership = org_member
    attachment = db.get(Attachment, attachment_id)
    if attachment is None or attachment.organization_id != org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found.")

    # Only uploader or admin+ can delete
    is_uploader = attachment.uploaded_by_user_id == membership.user_id
    is_admin = membership.role in ("admin", "owner")
    if not is_uploader and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the uploader or an admin can delete this attachment.",
        )

    # Delete from S3
    storage = get_storage()
    storage.delete_file(attachment.s3_key)

    write_audit(
        db,
        organization_id=org.id,
        actor_user_id=membership.user_id,
        action="attachment.deleted",
        resource_type="attachment",
        resource_id=str(attachment.id),
        metadata={"filename": attachment.filename, "task_id": str(attachment.task_id)},
    )
    db.delete(attachment)
    db.commit()
