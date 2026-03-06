"""Tasks repository — DB queries for the tasks domain."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.label import Label
from app.db.models.membership import Membership
from app.db.models.project import Project
from app.db.models.task import Task
from app.db.models.task_label import TaskLabel


def get_project_by_id(db: Session, project_id: uuid.UUID) -> Project | None:
    return db.get(Project, project_id)


def load_task(db: Session, org_id: uuid.UUID, task_id: uuid.UUID) -> Task | None:
    return db.scalars(
        select(Task)
        .where(Task.id == task_id, Task.organization_id == org_id, Task.deleted_at.is_(None))
        .options(selectinload(Task.task_labels).selectinload(TaskLabel.label))
    ).first()


def get_or_create_label(db: Session, org_id: uuid.UUID, name: str, color: str | None) -> Label:
    label = db.scalars(select(Label).where(Label.organization_id == org_id, Label.name == name)).first()
    if label is None:
        label = Label(organization_id=org_id, name=name, color=color)
        db.add(label)
        db.flush()
    return label


def get_task_label_link(db: Session, task_id: uuid.UUID, label_id: uuid.UUID) -> TaskLabel | None:
    return db.scalars(select(TaskLabel).where(TaskLabel.task_id == task_id, TaskLabel.label_id == label_id)).first()


def get_label_by_name(db: Session, org_id: uuid.UUID, name: str) -> Label | None:
    return db.scalars(select(Label).where(Label.organization_id == org_id, Label.name == name)).first()


def get_active_membership(db: Session, org_id: uuid.UUID, user_id: uuid.UUID) -> Membership | None:
    return db.scalars(select(Membership).where(Membership.organization_id == org_id, Membership.user_id == user_id, Membership.status == "active")).first()
