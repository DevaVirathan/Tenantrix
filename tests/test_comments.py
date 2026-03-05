"""Tests for M6 — comment endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

# --------------------------------------------------------------------------- #
# Shared helpers (mirrors test_tasks.py pattern)                               #
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


def _create_comment(client, token, org_id, task_id, body="Great work!"):
    r = client.post(
        f"/api/v1/organizations/{org_id}/tasks/{task_id}/comments",
        json={"body": body},
        headers=_auth(token),
    )
    assert r.status_code == 201, r.text
    return r.json()


# --------------------------------------------------------------------------- #
# Fixtures shorthand                                                            #
# --------------------------------------------------------------------------- #


def _setup(client):
    """Return (owner_token, org, project, task)."""
    token = _login(client, _register(client, "owner@c.com")["email"])
    org = _create_org(client, token)
    proj = _create_project(client, token, org["id"])
    task = _create_task(client, token, org["id"], proj["id"])
    return token, org, proj, task


# --------------------------------------------------------------------------- #
# POST /organizations/{org_id}/tasks/{task_id}/comments                        #
# --------------------------------------------------------------------------- #


class TestCreateComment:
    def test_create_ok(self, client):
        token, org, _, task = _setup(client)
        data = _create_comment(client, token, org["id"], task["id"], "Hello world")
        assert data["body"] == "Hello world"
        assert data["task_id"] == task["id"]
        assert data["organization_id"] == org["id"]
        assert data["deleted_at"] is None
        assert data["author_user_id"] is not None

    def test_create_requires_auth(self, client):
        _, org, _, task = _setup(client)
        r = client.post(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}/comments",
            json={"body": "No auth"},
        )
        assert r.status_code in (401, 403)

    def test_create_requires_membership(self, client):
        _token, org, _, task = _setup(client)
        outsider = _login(client, _register(client, "out@c.com")["email"])
        r = client.post(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}/comments",
            json={"body": "Sneaky"},
            headers=_auth(outsider),
        )
        assert r.status_code in (401, 403)

    def test_create_member_can_comment(self, client):
        token, org, _, task = _setup(client)
        member = _invite_and_join(client, token, org["id"], "mem@c.com")
        data = _create_comment(client, member, org["id"], task["id"], "Member comment")
        assert data["body"] == "Member comment"

    def test_create_on_nonexistent_task_404(self, client):
        token, org, _, _ = _setup(client)
        fake_id = "00000000-0000-0000-0000-000000000099"
        r = client.post(
            f"/api/v1/organizations/{org['id']}/tasks/{fake_id}/comments",
            json={"body": "Ghost"},
            headers=_auth(token),
        )
        assert r.status_code == 404

    def test_create_empty_body_422(self, client):
        token, org, _, task = _setup(client)
        r = client.post(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}/comments",
            json={"body": ""},
            headers=_auth(token),
        )
        assert r.status_code == 422

    def test_create_on_deleted_task_404(self, client):
        token, org, _, task = _setup(client)
        # Soft-delete the task first
        r = client.delete(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}",
            headers=_auth(token),
        )
        assert r.status_code == 204
        r = client.post(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}/comments",
            json={"body": "After delete"},
            headers=_auth(token),
        )
        assert r.status_code == 404


# --------------------------------------------------------------------------- #
# GET /organizations/{org_id}/tasks/{task_id}/comments                         #
# --------------------------------------------------------------------------- #


class TestListComments:
    def test_list_empty(self, client):
        token, org, _, task = _setup(client)
        r = client.get(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}/comments",
            headers=_auth(token),
        )
        assert r.status_code == 200
        assert r.json() == []

    def test_list_returns_comments(self, client):
        token, org, _, task = _setup(client)
        _create_comment(client, token, org["id"], task["id"], "First")
        _create_comment(client, token, org["id"], task["id"], "Second")
        r = client.get(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}/comments",
            headers=_auth(token),
        )
        assert r.status_code == 200
        bodies = [c["body"] for c in r.json()]
        assert bodies == ["First", "Second"]

    def test_list_excludes_deleted(self, client):
        token, org, _, task = _setup(client)
        c = _create_comment(client, token, org["id"], task["id"], "Will be deleted")
        _create_comment(client, token, org["id"], task["id"], "Survives")
        client.delete(
            f"/api/v1/organizations/{org['id']}/comments/{c['id']}",
            headers=_auth(token),
        )
        r = client.get(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}/comments",
            headers=_auth(token),
        )
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["body"] == "Survives"

    def test_list_requires_membership(self, client):
        _token, org, _, task = _setup(client)
        outsider = _login(client, _register(client, "out2@c.com")["email"])
        r = client.get(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}/comments",
            headers=_auth(outsider),
        )
        assert r.status_code in (401, 403)

    def test_list_task_not_found_404(self, client):
        token, org, _, _ = _setup(client)
        fake_id = "00000000-0000-0000-0000-000000000098"
        r = client.get(
            f"/api/v1/organizations/{org['id']}/tasks/{fake_id}/comments",
            headers=_auth(token),
        )
        assert r.status_code == 404


# --------------------------------------------------------------------------- #
# PATCH /organizations/{org_id}/comments/{comment_id}                          #
# --------------------------------------------------------------------------- #


class TestUpdateComment:
    def test_author_can_edit(self, client):
        token, org, _, task = _setup(client)
        c = _create_comment(client, token, org["id"], task["id"], "Original")
        r = client.patch(
            f"/api/v1/organizations/{org['id']}/comments/{c['id']}",
            json={"body": "Edited"},
            headers=_auth(token),
        )
        assert r.status_code == 200
        assert r.json()["body"] == "Edited"

    def test_admin_can_edit_others_comment(self, client):
        token, org, _, task = _setup(client)
        admin_token = _invite_and_join(client, token, org["id"], "adm@c.com", role="admin")
        # Owner creates comment
        c = _create_comment(client, token, org["id"], task["id"], "Owner comment")
        # Admin edits it
        r = client.patch(
            f"/api/v1/organizations/{org['id']}/comments/{c['id']}",
            json={"body": "Admin edited"},
            headers=_auth(admin_token),
        )
        assert r.status_code == 200
        assert r.json()["body"] == "Admin edited"

    def test_member_cannot_edit_others_comment(self, client):
        token, org, _, task = _setup(client)
        member = _invite_and_join(client, token, org["id"], "m2@c.com")
        c = _create_comment(client, token, org["id"], task["id"], "Owner comment")
        r = client.patch(
            f"/api/v1/organizations/{org['id']}/comments/{c['id']}",
            json={"body": "Stolen edit"},
            headers=_auth(member),
        )
        assert r.status_code == 403

    def test_update_not_found_404(self, client):
        token, org, _, _ = _setup(client)
        fake_id = "00000000-0000-0000-0000-000000000097"
        r = client.patch(
            f"/api/v1/organizations/{org['id']}/comments/{fake_id}",
            json={"body": "Ghost"},
            headers=_auth(token),
        )
        assert r.status_code == 404

    def test_update_empty_body_422(self, client):
        token, org, _, task = _setup(client)
        c = _create_comment(client, token, org["id"], task["id"], "Original")
        r = client.patch(
            f"/api/v1/organizations/{org['id']}/comments/{c['id']}",
            json={"body": ""},
            headers=_auth(token),
        )
        assert r.status_code == 422


# --------------------------------------------------------------------------- #
# DELETE /organizations/{org_id}/comments/{comment_id}                         #
# --------------------------------------------------------------------------- #


class TestDeleteComment:
    def test_author_can_delete(self, client):
        token, org, _, task = _setup(client)
        c = _create_comment(client, token, org["id"], task["id"])
        r = client.delete(
            f"/api/v1/organizations/{org['id']}/comments/{c['id']}",
            headers=_auth(token),
        )
        assert r.status_code == 204

    def test_soft_delete_hides_comment(self, client):
        token, org, _, task = _setup(client)
        c = _create_comment(client, token, org["id"], task["id"])
        client.delete(
            f"/api/v1/organizations/{org['id']}/comments/{c['id']}",
            headers=_auth(token),
        )
        r = client.get(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}/comments",
            headers=_auth(token),
        )
        assert r.json() == []

    def test_admin_can_delete_others_comment(self, client):
        token, org, _, task = _setup(client)
        admin_token = _invite_and_join(client, token, org["id"], "adm2@c.com", role="admin")
        c = _create_comment(client, token, org["id"], task["id"])
        r = client.delete(
            f"/api/v1/organizations/{org['id']}/comments/{c['id']}",
            headers=_auth(admin_token),
        )
        assert r.status_code == 204

    def test_member_cannot_delete_others_comment(self, client):
        token, org, _, task = _setup(client)
        member = _invite_and_join(client, token, org["id"], "m3@c.com")
        c = _create_comment(client, token, org["id"], task["id"])
        r = client.delete(
            f"/api/v1/organizations/{org['id']}/comments/{c['id']}",
            headers=_auth(member),
        )
        assert r.status_code == 403

    def test_delete_not_found_404(self, client):
        token, org, _, _ = _setup(client)
        fake_id = "00000000-0000-0000-0000-000000000096"
        r = client.delete(
            f"/api/v1/organizations/{org['id']}/comments/{fake_id}",
            headers=_auth(token),
        )
        assert r.status_code == 404

    def test_double_delete_404(self, client):
        token, org, _, task = _setup(client)
        c = _create_comment(client, token, org["id"], task["id"])
        client.delete(
            f"/api/v1/organizations/{org['id']}/comments/{c['id']}",
            headers=_auth(token),
        )
        r = client.delete(
            f"/api/v1/organizations/{org['id']}/comments/{c['id']}",
            headers=_auth(token),
        )
        assert r.status_code == 404
