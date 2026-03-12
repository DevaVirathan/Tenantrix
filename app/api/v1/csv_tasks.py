"""CSV import/export endpoints for tasks."""

from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import OrgAdmin, OrgMember
from app.db.session import get_db
from app.models.project import Project
from app.models.project_state import ProjectState
from app.models.sprint import Sprint
from app.models.task import IssueType, Task, TaskPriority, TaskStatus
from app.models.user import User
from app.schemas.task import CSVImportResponse
from app.services.audit import write_audit

router = APIRouter(prefix="/organizations/{org_id}", tags=["csv-tasks"])

_CSV_COLUMNS = [
    "identifier",
    "title",
    "description",
    "status",
    "priority",
    "issue_type",
    "assignee",
    "state",
    "sprint",
    "story_points",
    "start_date",
    "due_date",
    "created_at",
]


def _get_project_or_404(db: Session, org_id: uuid.UUID, project_id: uuid.UUID) -> Project:
    project = db.get(Project, project_id)
    if project is None or project.organization_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return project


# --------------------------------------------------------------------------- #
# GET /…/tasks/export/csv                                                      #
# --------------------------------------------------------------------------- #


@router.get("/projects/{project_id}/tasks/export/csv")
def export_tasks_csv(
    org_member: OrgMember,
    project_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> StreamingResponse:
    """Export all active tasks in a project as a CSV file (MEMBER+ required)."""
    org, _membership = org_member
    project = _get_project_or_404(db, org.id, project_id)

    tasks = db.scalars(
        select(Task)
        .where(
            Task.project_id == project_id,
            Task.organization_id == org.id,
            Task.deleted_at.is_(None),
        )
        .options(
            selectinload(Task.assignee),
            selectinload(Task.state),
            selectinload(Task.sprint),
        )
        .order_by(Task.sequence_id)
    ).all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(_CSV_COLUMNS)

    for t in tasks:
        identifier = f"{project.identifier}-{t.sequence_id}" if t.sequence_id else ""
        assignee_name = ""
        if t.assignee:
            assignee_name = t.assignee.full_name or t.assignee.email
        state_name = t.state.name if t.state else ""
        sprint_name = t.sprint.name if t.sprint else ""

        writer.writerow([
            identifier,
            t.title,
            t.description or "",
            t.status.value if t.status else "",
            t.priority.value if t.priority else "",
            t.issue_type.value if t.issue_type else "",
            assignee_name,
            state_name,
            sprint_name,
            t.story_points if t.story_points is not None else "",
            t.start_date.isoformat() if t.start_date else "",
            t.due_date.isoformat() if t.due_date else "",
            t.created_at.isoformat() if t.created_at else "",
        ])

    buf.seek(0)
    filename = f"{project.identifier}_tasks.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --------------------------------------------------------------------------- #
# POST /…/tasks/import/csv                                                     #
# --------------------------------------------------------------------------- #


@router.post(
    "/projects/{project_id}/tasks/import/csv",
    response_model=CSVImportResponse,
    status_code=status.HTTP_201_CREATED,
)
def import_tasks_csv(
    org_admin: OrgAdmin,
    file: UploadFile,
    project_id: uuid.UUID = Path(...),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> CSVImportResponse:
    """Import tasks from a CSV file (ADMIN+ required).

    Required columns: title
    Optional columns: description, priority, issue_type, story_points, start_date, due_date
    """
    org, _membership = org_admin
    _get_project_or_404(db, org.id, project_id)

    if file.content_type and file.content_type not in ("text/csv", "application/octet-stream"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File must be a CSV.",
        )

    try:
        content = file.file.read().decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File is not valid UTF-8.",
        ) from exc

    reader = csv.DictReader(io.StringIO(content))
    if reader.fieldnames is None or "title" not in [f.strip().lower() for f in reader.fieldnames]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CSV must contain a 'title' column.",
        )

    # Normalise header names
    reader.fieldnames = [f.strip().lower() for f in reader.fieldnames]

    # Get default state for the project
    default_state = db.scalars(
        select(ProjectState)
        .where(ProjectState.project_id == project_id, ProjectState.is_default.is_(True))
    ).first()

    # Lock project for sequence_id increments
    locked_project = db.scalars(
        select(Project).where(Project.id == project_id).with_for_update()
    ).one()

    imported_count = 0
    errors: list[str] = []

    for row_num, row in enumerate(reader, start=2):  # row 1 is header
        title = (row.get("title") or "").strip()
        if not title:
            errors.append(f"Row {row_num}: missing title, skipped.")
            continue

        # Parse optional fields
        priority_str = (row.get("priority") or "medium").strip().lower()
        try:
            priority = TaskPriority(priority_str)
        except ValueError:
            priority = TaskPriority.MEDIUM
            errors.append(f"Row {row_num}: invalid priority '{priority_str}', defaulting to medium.")

        issue_type_str = (row.get("issue_type") or "task").strip().lower()
        try:
            issue_type = IssueType(issue_type_str)
        except ValueError:
            issue_type = IssueType.TASK
            errors.append(f"Row {row_num}: invalid issue_type '{issue_type_str}', defaulting to task.")

        story_points = None
        sp_str = (row.get("story_points") or "").strip()
        if sp_str:
            try:
                story_points = int(sp_str)
            except ValueError:
                errors.append(f"Row {row_num}: invalid story_points '{sp_str}', skipping field.")

        start_date = None
        sd_str = (row.get("start_date") or "").strip()
        if sd_str:
            try:
                start_date = datetime.fromisoformat(sd_str)
            except ValueError:
                errors.append(f"Row {row_num}: invalid start_date '{sd_str}', skipping field.")

        due_date = None
        dd_str = (row.get("due_date") or "").strip()
        if dd_str:
            try:
                due_date = datetime.fromisoformat(dd_str)
            except ValueError:
                errors.append(f"Row {row_num}: invalid due_date '{dd_str}', skipping field.")

        locked_project.issue_sequence += 1
        sequence_id = locked_project.issue_sequence

        task = Task(
            organization_id=org.id,
            project_id=project_id,
            title=title,
            description=(row.get("description") or "").strip() or None,
            state_id=default_state.id if default_state else None,
            sequence_id=sequence_id,
            status=TaskStatus.TODO,
            priority=priority,
            issue_type=issue_type,
            created_by_user_id=_membership.user_id,
            story_points=story_points,
            start_date=start_date,
            due_date=due_date,
        )
        db.add(task)
        imported_count += 1

    if imported_count > 0:
        write_audit(
            db,
            organization_id=org.id,
            actor_user_id=_membership.user_id,
            action="task.csv_imported",
            resource_type="task",
            resource_id="csv_import",
            metadata={"imported_count": imported_count, "project_id": str(project_id)},
        )
        db.commit()

    return CSVImportResponse(imported_count=imported_count, errors=errors)
