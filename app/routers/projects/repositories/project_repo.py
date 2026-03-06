"""Projects repository — DB queries for the projects domain."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.db.models.project import Project


def get_project_by_id(db: Session, project_id: uuid.UUID) -> Project | None:
    return db.get(Project, project_id)
