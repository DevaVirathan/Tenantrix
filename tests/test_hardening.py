"""Tests for M8/M9 — middleware, error handling, org endpoints, password strength."""

from __future__ import annotations

from fastapi.testclient import TestClient

# --------------------------------------------------------------------------- #
# Helpers                                                                       #
# --------------------------------------------------------------------------- #


def _register(client: TestClient, email: str, password: str = "StrongP@ss1") -> dict:
    r = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201, r.text
    return r.json()


def _login(client: TestClient, email: str, password: str = "StrongP@ss1") -> str:
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_org(client, token, name="Acme", slug="acme") -> dict:
    r = client.post("/api/v1/organizations", json={"name": name, "slug": slug}, headers=_auth(token))
    assert r.status_code == 201, r.text
    return r.json()


def _invite_and_join(client, owner_token, org_id, email, role="member") -> str:
    _register(client, email)
    member_token = _login(client, email)
    r = client.post(
        f"/api/v1/organizations/{org_id}/invites",
        json={"email": email, "role": role},
        headers=_auth(owner_token),
    )
    assert r.status_code == 201, r.text
    r = client.post(
        f"/api/v1/organizations/invites/accept/{r.json()['token']}",
        headers=_auth(member_token),
    )
    assert r.status_code == 200, r.text
    return member_token


# --------------------------------------------------------------------------- #
# M8: X-Request-ID middleware                                                  #
# --------------------------------------------------------------------------- #


class TestRequestIDMiddleware:
    def test_response_has_request_id_header(self, client):
        r = client.get("/api/v1/health")
        assert "x-request-id" in r.headers

    def test_request_id_is_valid_uuid(self, client):
        import uuid
        r = client.get("/api/v1/health")
        rid = r.headers["x-request-id"]
        uuid.UUID(rid)  # raises ValueError if not a valid UUID

    def test_client_supplied_request_id_is_echoed(self, client):
        import uuid
        supplied = str(uuid.uuid4())
        r = client.get("/api/v1/health", headers={"X-Request-ID": supplied})
        assert r.headers["x-request-id"] == supplied

    def test_invalid_client_request_id_gets_replaced(self, client):
        import uuid
        r = client.get("/api/v1/health", headers={"X-Request-ID": "not-a-uuid"})
        rid = r.headers["x-request-id"]
        # Should have generated a fresh valid UUID
        uuid.UUID(rid)
        assert rid != "not-a-uuid"


# --------------------------------------------------------------------------- #
# M9: Security headers middleware                                              #
# --------------------------------------------------------------------------- #


class TestSecurityHeaders:
    def test_x_content_type_options(self, client):
        r = client.get("/api/v1/health")
        assert r.headers.get("x-content-type-options") == "nosniff"

    def test_x_frame_options(self, client):
        r = client.get("/api/v1/health")
        assert r.headers.get("x-frame-options") == "DENY"

    def test_referrer_policy(self, client):
        r = client.get("/api/v1/health")
        assert r.headers.get("referrer-policy") == "strict-origin-when-cross-origin"

    def test_permissions_policy(self, client):
        r = client.get("/api/v1/health")
        assert "permissions-policy" in r.headers


# --------------------------------------------------------------------------- #
# M8: Error envelope                                                           #
# --------------------------------------------------------------------------- #


class TestErrorEnvelope:
    def test_404_uses_error_envelope(self, client):
        r = client.get("/api/v1/organizations/00000000-0000-0000-0000-000000000001")
        assert r.status_code in (401, 403, 404)
        # Unauthenticated gets 401 — body should be envelope
        data = r.json()
        assert "error" in data

    def test_401_uses_error_envelope(self, client):
        r = client.get("/api/v1/auth/me")
        assert r.status_code == 401
        data = r.json()
        assert "error" in data
        assert "detail" in data["error"]

    def test_422_uses_error_envelope(self, client):
        r = client.post("/api/v1/auth/register", json={"email": "bad"})
        assert r.status_code == 422
        data = r.json()
        assert "error" in data

    def test_error_envelope_contains_request_id(self, client):
        import uuid
        rid = str(uuid.uuid4())
        r = client.get("/api/v1/auth/me", headers={"X-Request-ID": rid})
        assert r.status_code == 401
        data = r.json()
        assert data["error"]["request_id"] == rid


# --------------------------------------------------------------------------- #
# M8: GET /organizations — list current user's orgs                           #
# --------------------------------------------------------------------------- #


class TestListOrganizations:
    def test_returns_empty_for_new_user(self, client):
        token = _login(client, _register(client, "lo1@h.com")["email"])
        # Create no org — should be empty (user has no memberships yet)
        # Actually after register user has no org, so:
        # We need to call list before creating
        r = client.get("/api/v1/organizations", headers=_auth(token))
        assert r.status_code == 200
        assert r.json() == []

    def test_returns_created_orgs(self, client):
        token = _login(client, _register(client, "lo2@h.com")["email"])
        _create_org(client, token)
        r = client.get("/api/v1/organizations", headers=_auth(token))
        assert r.status_code == 200
        orgs = r.json()
        assert len(orgs) == 1
        assert orgs[0]["slug"] == "acme"

    def test_shows_joined_org(self, client):
        owner_token = _login(client, _register(client, "lo3@h.com")["email"])
        org = _create_org(client, owner_token)
        member_token = _invite_and_join(client, owner_token, org["id"], "lo4@h.com")
        r = client.get("/api/v1/organizations", headers=_auth(member_token))
        assert r.status_code == 200
        slugs = [o["slug"] for o in r.json()]
        assert "acme" in slugs

    def test_cross_user_isolation(self, client):
        t1 = _login(client, _register(client, "lo5@h.com")["email"])
        t2 = _login(client, _register(client, "lo6@h.com")["email"])
        _create_org(client, t1, name="OrgA", slug="orga")
        _create_org(client, t2, name="OrgB", slug="orgb")
        orgs1 = [o["slug"] for o in client.get("/api/v1/organizations", headers=_auth(t1)).json()]
        orgs2 = [o["slug"] for o in client.get("/api/v1/organizations", headers=_auth(t2)).json()]
        assert "orga" in orgs1 and "orgb" not in orgs1
        assert "orgb" in orgs2 and "orga" not in orgs2

    def test_requires_auth(self, client):
        r = client.get("/api/v1/organizations")
        assert r.status_code in (401, 403)


# --------------------------------------------------------------------------- #
# M8: PATCH /organizations/{org_id} — update org (OWNER)                      #
# --------------------------------------------------------------------------- #


class TestUpdateOrganization:
    def test_owner_can_update_name(self, client):
        token = _login(client, _register(client, "uo1@h.com")["email"])
        org = _create_org(client, token)
        r = client.patch(
            f"/api/v1/organizations/{org['id']}",
            json={"name": "New Name"},
            headers=_auth(token),
        )
        assert r.status_code == 200
        assert r.json()["name"] == "New Name"

    def test_owner_can_update_description(self, client):
        token = _login(client, _register(client, "uo2@h.com")["email"])
        org = _create_org(client, token)
        r = client.patch(
            f"/api/v1/organizations/{org['id']}",
            json={"description": "A great org"},
            headers=_auth(token),
        )
        assert r.status_code == 200
        assert r.json()["description"] == "A great org"

    def test_admin_cannot_update(self, client):
        token = _login(client, _register(client, "uo3@h.com")["email"])
        org = _create_org(client, token)
        admin_token = _invite_and_join(client, token, org["id"], "uo4@h.com", role="admin")
        r = client.patch(
            f"/api/v1/organizations/{org['id']}",
            json={"name": "Hacked"},
            headers=_auth(admin_token),
        )
        assert r.status_code in (401, 403)

    def test_member_cannot_update(self, client):
        token = _login(client, _register(client, "uo5@h.com")["email"])
        org = _create_org(client, token)
        member_token = _invite_and_join(client, token, org["id"], "uo6@h.com")
        r = client.patch(
            f"/api/v1/organizations/{org['id']}",
            json={"name": "Hacked"},
            headers=_auth(member_token),
        )
        assert r.status_code in (401, 403)

    def test_update_emits_audit_event(self, client):
        token = _login(client, _register(client, "uo7@h.com")["email"])
        org = _create_org(client, token)
        client.patch(
            f"/api/v1/organizations/{org['id']}",
            json={"name": "Renamed"},
            headers=_auth(token),
        )
        logs = client.get(
            f"/api/v1/organizations/{org['id']}/audit-logs",
            headers=_auth(token),
        ).json()
        actions = [lg["action"] for lg in logs]
        assert "org.updated" in actions

    def test_partial_update_leaves_other_fields_unchanged(self, client):
        token = _login(client, _register(client, "uo8@h.com")["email"])
        org = _create_org(client, token, name="Original", slug="original")
        r = client.patch(
            f"/api/v1/organizations/{org['id']}",
            json={"description": "Just a desc"},
            headers=_auth(token),
        )
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Original"  # unchanged
        assert data["slug"] == "original"  # unchanged
        assert data["description"] == "Just a desc"


# --------------------------------------------------------------------------- #
# M9: Password strength validator                                              #
# --------------------------------------------------------------------------- #


class TestPasswordStrength:
    def test_rejects_no_uppercase(self, client):
        r = client.post(
            "/api/v1/auth/register",
            json={"email": "ps1@h.com", "password": "weakpass@1"},
        )
        assert r.status_code == 422

    def test_rejects_no_lowercase(self, client):
        r = client.post(
            "/api/v1/auth/register",
            json={"email": "ps2@h.com", "password": "WEAKPASS@1"},
        )
        assert r.status_code == 422

    def test_rejects_no_digit(self, client):
        r = client.post(
            "/api/v1/auth/register",
            json={"email": "ps3@h.com", "password": "WeakPass@"},
        )
        assert r.status_code == 422

    def test_rejects_no_special_char(self, client):
        r = client.post(
            "/api/v1/auth/register",
            json={"email": "ps4@h.com", "password": "WeakPass1"},
        )
        assert r.status_code == 422

    def test_accepts_strong_password(self, client):
        r = client.post(
            "/api/v1/auth/register",
            json={"email": "ps5@h.com", "password": "StrongP@ss1"},
        )
        assert r.status_code == 201

    def test_rejects_too_short(self, client):
        r = client.post(
            "/api/v1/auth/register",
            json={"email": "ps6@h.com", "password": "S@1a"},
        )
        assert r.status_code == 422
