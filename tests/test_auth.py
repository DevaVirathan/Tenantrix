"""M2 tests — auth endpoints: register, login, refresh, logout, me."""

from __future__ import annotations

from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _register(client: TestClient, email: str, password: str = "Secret123") -> dict:
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    return resp


def _login(client: TestClient, email: str, password: str = "Secret123") -> dict:
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------


def test_register_success(client: TestClient):
    resp = _register(client, "alice@example.com")
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "alice@example.com"
    assert "id" in data
    assert "password_hash" not in data


def test_register_lowercases_email(client: TestClient):
    resp = _register(client, "BOB@Example.COM")
    assert resp.status_code == 201
    assert resp.json()["email"] == "bob@example.com"


def test_register_duplicate_email(client: TestClient):
    _register(client, "carol@example.com")
    resp = _register(client, "carol@example.com")
    assert resp.status_code == 409


def test_register_password_too_short(client: TestClient):
    resp = _register(client, "dave@example.com", password="abc1")
    assert resp.status_code == 422


def test_register_password_all_digits(client: TestClient):
    resp = _register(client, "eve@example.com", password="12345678")
    assert resp.status_code == 422


def test_register_password_all_letters(client: TestClient):
    resp = _register(client, "frank@example.com", password="abcdefgh")
    assert resp.status_code == 422


def test_register_invalid_email(client: TestClient):
    resp = _register(client, "not-an-email", password="Secret123")
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------


def test_login_success(client: TestClient):
    _register(client, "grace@example.com")
    resp = _login(client, "grace@example.com")
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    from app.core.config import settings
    assert data["expires_in"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


def test_login_wrong_password(client: TestClient):
    _register(client, "henry@example.com")
    resp = _login(client, "henry@example.com", password="WrongPass1")
    assert resp.status_code == 401


def test_login_unknown_email(client: TestClient):
    resp = _login(client, "ghost@example.com")
    assert resp.status_code == 401


def test_login_case_insensitive_email(client: TestClient):
    _register(client, "iris@example.com")
    resp = _login(client, "IRIS@EXAMPLE.COM")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# POST /auth/refresh
# ---------------------------------------------------------------------------


def test_refresh_success(client: TestClient):
    _register(client, "jake@example.com")
    login_resp = _login(client, "jake@example.com")
    refresh_token = login_resp.json()["refresh_token"]

    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    # new refresh token must differ from the old one
    assert data["refresh_token"] != refresh_token


def test_refresh_token_rotation_invalidates_old(client: TestClient):
    _register(client, "kim@example.com")
    login_resp = _login(client, "kim@example.com")
    old_refresh = login_resp.json()["refresh_token"]

    # Use the old token once
    client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})

    # Try to use the old token again — must be rejected
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert resp.status_code == 401


def test_refresh_reuse_detection_invalidates_family(client: TestClient):
    """Using a revoked token must invalidate all tokens in the family."""
    _register(client, "leo@example.com")
    login_resp = _login(client, "leo@example.com")
    old_refresh = login_resp.json()["refresh_token"]

    # Rotate once to get new token
    resp1 = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    new_refresh = resp1.json()["refresh_token"]

    # Reuse the old (already revoked) token — triggers family wipe
    client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})

    # The new token from the same family must also be dead now
    resp2 = client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})
    assert resp2.status_code == 401


def test_refresh_invalid_token(client: TestClient):
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": "totally-fake"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------


def test_logout_success(client: TestClient):
    _register(client, "mia@example.com")
    login_resp = _login(client, "mia@example.com")
    refresh_token = login_resp.json()["refresh_token"]

    resp = client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert resp.json()["message"] == "Logged out successfully."


def test_logout_revoked_token_returns_200(client: TestClient):
    """Logout is idempotent — returns 200 even for unknown tokens."""
    resp = client.post("/api/v1/auth/logout", json={"refresh_token": "no-such-token"})
    assert resp.status_code == 200


def test_logout_prevents_refresh(client: TestClient):
    _register(client, "noah@example.com")
    login_resp = _login(client, "noah@example.com")
    refresh_token = login_resp.json()["refresh_token"]

    client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})

    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------


def test_me_success(client: TestClient):
    _register(client, "olivia@example.com")
    login_resp = _login(client, "olivia@example.com")
    access_token = login_resp.json()["access_token"]

    resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "olivia@example.com"


def test_me_no_token(client: TestClient):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_invalid_token(client: TestClient):
    resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer garbage.token.here"},
    )
    assert resp.status_code == 401


def test_me_expired_token(client: TestClient):
    """Simulate an expired JWT by creating one with past expiry."""
    from datetime import UTC, datetime, timedelta

    import jwt

    from app.core.config import settings

    payload = {
        "sub": "00000000-0000-0000-0000-000000000001",
        "iat": datetime.now(UTC) - timedelta(hours=2),
        "exp": datetime.now(UTC) - timedelta(hours=1),
        "type": "access",
    }
    expired = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired}"},
    )
    assert resp.status_code == 401
