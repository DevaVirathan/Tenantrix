"""Security utilities — password hashing, JWT tokens, refresh tokens."""
from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from passlib.context import CryptContext

from app.core.config import settings

# --------------------------------------------------------------------------- #
# Password hashing                                                            #
# --------------------------------------------------------------------------- #
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of the given plaintext password."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if the plaintext matches the stored hash."""
    return _pwd_context.verify(plain, hashed)


# --------------------------------------------------------------------------- #
# JWT — access tokens                                                         #
# --------------------------------------------------------------------------- #
def create_access_token(subject: str) -> str:
    """Create a signed JWT access token with the user id as the subject."""
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and verify a JWT access token.

    Raises jwt.PyJWTError (including ExpiredSignatureError) on failure.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


# --------------------------------------------------------------------------- #
# Refresh tokens — opaque random tokens                                       #
# --------------------------------------------------------------------------- #
def generate_refresh_token() -> tuple[str, str]:
    """
    Return (raw_token, token_hash).

    The raw token is sent to the client; only the SHA-256 hash is stored in DB.
    """
    raw = secrets.token_urlsafe(48)
    token_hash = _hash_token(raw)
    return raw, token_hash


def hash_refresh_token(raw: str) -> str:
    """SHA-256 hash a raw refresh token for DB lookup."""
    return _hash_token(raw)


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def refresh_token_expiry() -> datetime:
    """Return the expiry datetime for a new refresh token."""
    return datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
