"""Auth repository — DB queries for auth domain."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.refresh_token import RefreshToken
from app.db.models.user import User


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email.lower()).first()


def get_user_by_id(db: Session, user_id) -> User | None:
    return db.get(User, user_id)


def get_refresh_token_by_hash(db: Session, token_hash: str) -> RefreshToken | None:
    return db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()


def get_refresh_tokens_by_family(db: Session, family_id) -> list[RefreshToken]:
    return db.query(RefreshToken).filter(RefreshToken.family_id == family_id).all()
