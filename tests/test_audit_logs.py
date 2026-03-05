"""Tests for M7 — audit log endpoints."""

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


def _create_org(client, token, name="Acme", slug="acme"):
    r = client.post("/api/v1/organizations", json={"name": name, "slug": slug}, headers=_auth(token))
    assert r.status_code == 201, r.text
    return r.json()


def _invite_and_join(client, owner_token, org_id, email, role="member"):
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


def _create_project(client, token, org_id, name="Alpha"):
    r = client.post(
        f"/api/v1/organizations/{org_id}/projects",
        json={"name": name},
        headers=_auth(token),
    )
    assert r.status_code == 201, r.text
    return r.json()


def _create_task(client, token, org_id, project_id, title="Fix bug"):
    r = client.post(
        f"/api/v1/organizations/{org_id}/projects/{project_id}/tasks",
        json={"title": title},
        headers=_auth(token),
    )
    assert r.status_code == 201, r.text
    return r.json()


def _audit_logs(client, token, org_id, **params):
    r = client.get(
        f"/api/v1/organizations/{org_id}/audit-logs",
        headers=_auth(token),
        params=params,
    )
    assert r.status_code == 200, r.text
    return r.json()


def _setup(client):
    """Return (owner_token, org, project, task)."""
    token = _login(client, _register(client, "owner@al.com")["email"])
    org = _create_org(client, token)
    proj = _create_project(client, token, org["id"])
    task = _create_task(client, token, org["id"], proj["id"])
    return token, org, proj, task


# --------------------------------------------------------------------------- #
# Access control                                                                #
# --------------------------------------------------------------------------- #


class TestAuditLogAccess:
    def test_requires_auth(self, client):
        _token, org, _, _ = _setup(client)
        r = client.get(f"/api/v1/organizations/{org['id']}/audit-logs")
        assert r.status_code in (401, 403)

    def test_member_forbidden(self, client):
        token, org, _, _ = _setup(client)
        member = _invite_and_join(client, token, org["id"], "mem@al.com")
        r = client.get(
            f"/api/v1/organizations/{org['id']}/audit-logs",
            headers=_auth(member),
        )
        assert r.status_code in (401, 403)

    def test_admin_allowed(self, client):
        token, org, _, _ = _setup(client)
        admin = _invite_and_join(client, token, org["id"], "adm@al.com", role="admin")
        r = client.get(
            f"/api/v1/organizations/{org['id']}/audit-logs",
            headers=_auth(admin),
        )
        assert r.status_code == 200

    def test_owner_allowed(self, client):
        token, org, _, _ = _setup(client)
        r = client.get(
            f"/api/v1/organizations/{org['id']}/audit-logs",
            headers=_auth(token),
        )
        assert r.status_code == 200

    def test_outsider_forbidden(self, client):
        _token, org, _, _ = _setup(client)
        outsider = _login(client, _register(client, "out@al.com")["email"])
        r = client.get(
            f"/api/v1/organizations/{org['id']}/audit-logs",
            headers=_auth(outsider),
        )
        assert r.status_code in (401, 403)


# --------------------------------------------------------------------------- #
# Event emission                                                                #
# --------------------------------------------------------------------------- #


class TestAuditEvents:
    def test_org_created_event(self, client):
        token = _login(client, _register(client, "ev1@al.com")["email"])
        org = _create_org(client, token)
        logs = _audit_logs(client, token, org["id"])
        actions = [lg["action"] for lg in logs]
        assert "org.created" in actions

    def test_project_created_event(self, client):
        token, org, _, _ = _setup(client)
        logs = _audit_logs(client, token, org["id"])
        actions = [lg["action"] for lg in logs]
        assert "project.created" in actions

    def test_task_created_event(self, client):
        token, org, _, _ = _setup(client)
        logs = _audit_logs(client, token, org["id"])
        actions = [lg["action"] for lg in logs]
        assert "task.created" in actions

    def test_task_updated_event(self, client):
        token, org, _, task = _setup(client)
        client.patch(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}",
            json={"title": "New title"},
            headers=_auth(token),
        )
        logs = _audit_logs(client, token, org["id"])
        actions = [lg["action"] for lg in logs]
        assert "task.updated" in actions

    def test_task_deleted_event(self, client):
        token, org, _, task = _setup(client)
        client.delete(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}",
            headers=_auth(token),
        )
        logs = _audit_logs(client, token, org["id"])
        actions = [lg["action"] for lg in logs]
        assert "task.deleted" in actions

    def test_comment_created_event(self, client):
        token, org, _, task = _setup(client)
        client.post(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}/comments",
            json={"body": "Hello"},
            headers=_auth(token),
        )
        logs = _audit_logs(client, token, org["id"])
        actions = [lg["action"] for lg in logs]
        assert "comment.created" in actions

    def test_invite_sent_event(self, client):
        token, org, _, _ = _setup(client)
        _register(client, "inv@al.com")
        client.post(
            f"/api/v1/organizations/{org['id']}/invites",
            json={"email": "inv@al.com", "role": "member"},
            headers=_auth(token),
        )
        logs = _audit_logs(client, token, org["id"])
        actions = [lg["action"] for lg in logs]
        assert "invite.sent" in actions


# --------------------------------------------------------------------------- #
# Response shape                                                                #
# --------------------------------------------------------------------------- #


class TestAuditLogShape:
    def test_fields_present(self, client):
        token, org, _, _ = _setup(client)
        logs = _audit_logs(client, token, org["id"])
        assert len(logs) > 0
        entry = logs[0]
        for field in ("id", "organization_id", "actor_user_id", "action", "created_at"):
            assert field in entry, f"Missing field: {field}"

    def test_newest_first(self, client):
        token, org, proj, _ = _setup(client)
        _create_task(client, token, org["id"], proj["id"], title="Second task")
        logs = _audit_logs(client, token, org["id"])
        times = [lg["created_at"] for lg in logs]
        assert times == sorted(times, reverse=True)

    def test_metadata_populated(self, client):
        token, org, _, _ = _setup(client)
        logs = _audit_logs(client, token, org["id"], action="org.created")
        assert len(logs) == 1
        assert logs[0]["metadata"]["name"] == "Acme"


# --------------------------------------------------------------------------- #
# Filters                                                                       #
# --------------------------------------------------------------------------- #


class TestAuditLogFilters:
    def test_filter_by_action(self, client):
        token, org, _, task = _setup(client)
        client.patch(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}",
            json={"title": "X"},
            headers=_auth(token),
        )
        logs = _audit_logs(client, token, org["id"], action="task.updated")
        assert all(lg["action"] == "task.updated" for lg in logs)
        assert len(logs) >= 1

    def test_filter_by_resource_type(self, client):
        token, org, _, _ = _setup(client)
        logs = _audit_logs(client, token, org["id"], resource_type="task")
        assert all(lg["resource_type"] == "task" for lg in logs)

    def test_filter_by_resource_id(self, client):
        token, org, _, task = _setup(client)
        logs = _audit_logs(client, token, org["id"], resource_id=task["id"])
        assert all(lg["resource_id"] == task["id"] for lg in logs)
        assert len(logs) >= 1

    def test_pagination_limit(self, client):
        token, org, proj, _ = _setup(client)
        # Create extra tasks to pad the log
        for i in range(5):
            _create_task(client, token, org["id"], proj["id"], title=f"T{i}")
        logs = _audit_logs(client, token, org["id"], limit=2)
        assert len(logs) <= 2

    def test_pagination_offset(self, client):
        token, org, _, _ = _setup(client)
        all_logs = _audit_logs(client, token, org["id"])
        offset_logs = _audit_logs(client, token, org["id"], offset=1)
        assert len(offset_logs) == len(all_logs) - 1

    def test_cross_org_isolation(self, client):
        token1 = _login(client, _register(client, "o1@al.com")["email"])
        token2 = _login(client, _register(client, "o2@al.com")["email"])
        org1 = _create_org(client, token1, name="Org1", slug="org1")
        org2 = _create_org(client, token2, name="Org2", slug="org2")
        logs1 = _audit_logs(client, token1, org1["id"])
        logs2 = _audit_logs(client, token2, org2["id"])
        ids1 = {lg["id"] for lg in logs1}
        ids2 = {lg["id"] for lg in logs2}
        assert ids1.isdisjoint(ids2)
