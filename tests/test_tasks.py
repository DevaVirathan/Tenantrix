"""Tests for M5 — task management endpoints."""

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


def _create_task(client, token, org_id, project_id, title="Fix bug", **kwargs):
    payload = {"title": title, **kwargs}
    r = client.post(
        f"/api/v1/organizations/{org_id}/projects/{project_id}/tasks",
        json=payload,
        headers=_auth(token),
    )
    assert r.status_code == 201, r.text
    return r.json()


# --------------------------------------------------------------------------- #
# POST …/projects/{project_id}/tasks — create                                  #
# --------------------------------------------------------------------------- #


class TestCreateTask:
    def test_create_ok_defaults(self, client):
        token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, token)
        proj = _create_project(client, token, org["id"])
        data = _create_task(client, token, org["id"], proj["id"])
        assert data["title"] == "Fix bug"
        assert data["status"] == "todo"
        assert data["priority"] == "medium"
        assert data["labels"] == []
        assert data["deleted_at"] is None

    def test_create_with_all_fields(self, client):
        token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, token)
        proj = _create_project(client, token, org["id"])
        data = _create_task(
            client, token, org["id"], proj["id"],
            title="Ship feature",
            description="Important",
            status="in_progress",
            priority="high",
            position=5,
        )
        assert data["status"] == "in_progress"
        assert data["priority"] == "high"
        assert data["position"] == 5

    def test_create_with_assignee(self, client):
        owner_token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, owner_token)
        member_data = _register(client, "m@t.com")
        member_token = _login(client, "m@t.com")
        r = client.post(
            f"/api/v1/organizations/{org['id']}/invites",
            json={"email": "m@t.com", "role": "member"},
            headers=_auth(owner_token),
        )
        client.post(
            f"/api/v1/organizations/invites/accept/{r.json()['token']}",
            headers=_auth(member_token),
        )
        proj = _create_project(client, owner_token, org["id"])
        data = _create_task(
            client, owner_token, org["id"], proj["id"],
            assignee_user_id=member_data["id"],
        )
        assert data["assignee_user_id"] == member_data["id"]

    def test_create_assignee_not_member_422(self, client):
        owner_token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, owner_token)
        outsider = _register(client, "out@t.com")
        proj = _create_project(client, owner_token, org["id"])
        r = client.post(
            f"/api/v1/organizations/{org['id']}/projects/{proj['id']}/tasks",
            json={"title": "T", "assignee_user_id": outsider["id"]},
            headers=_auth(owner_token),
        )
        assert r.status_code == 422

    def test_create_requires_auth(self, client):
        token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, token)
        proj = _create_project(client, token, org["id"])
        r = client.post(
            f"/api/v1/organizations/{org['id']}/projects/{proj['id']}/tasks",
            json={"title": "T"},
        )
        assert r.status_code in (401, 403)

    def test_create_non_member_forbidden(self, client):
        owner_token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, owner_token)
        proj = _create_project(client, owner_token, org["id"])
        outsider_token = _login(client, _register(client, "out@t.com")["email"])
        r = client.post(
            f"/api/v1/organizations/{org['id']}/projects/{proj['id']}/tasks",
            json={"title": "T"},
            headers=_auth(outsider_token),
        )
        assert r.status_code == 403

    def test_create_project_not_found(self, client):
        token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, token)
        fake = "00000000-0000-0000-0000-000000000000"
        r = client.post(
            f"/api/v1/organizations/{org['id']}/projects/{fake}/tasks",
            json={"title": "T"},
            headers=_auth(token),
        )
        assert r.status_code == 404

    def test_create_missing_title_422(self, client):
        token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, token)
        proj = _create_project(client, token, org["id"])
        r = client.post(
            f"/api/v1/organizations/{org['id']}/projects/{proj['id']}/tasks",
            json={},
            headers=_auth(token),
        )
        assert r.status_code == 422


# --------------------------------------------------------------------------- #
# GET …/projects/{project_id}/tasks — list with filters                        #
# --------------------------------------------------------------------------- #


class TestListTasks:
    def test_list_empty(self, client):
        token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, token)
        proj = _create_project(client, token, org["id"])
        r = client.get(
            f"/api/v1/organizations/{org['id']}/projects/{proj['id']}/tasks",
            headers=_auth(token),
        )
        assert r.status_code == 200
        assert r.json() == []

    def test_list_multiple(self, client):
        token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, token)
        proj = _create_project(client, token, org["id"])
        _create_task(client, token, org["id"], proj["id"], title="T1")
        _create_task(client, token, org["id"], proj["id"], title="T2")
        r = client.get(
            f"/api/v1/organizations/{org['id']}/projects/{proj['id']}/tasks",
            headers=_auth(token),
        )
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_filter_by_status(self, client):
        token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, token)
        proj = _create_project(client, token, org["id"])
        _create_task(client, token, org["id"], proj["id"], title="Todo", status="todo")
        _create_task(client, token, org["id"], proj["id"], title="Done", status="done")
        r = client.get(
            f"/api/v1/organizations/{org['id']}/projects/{proj['id']}/tasks?status=todo",
            headers=_auth(token),
        )
        assert r.status_code == 200
        assert all(t["status"] == "todo" for t in r.json())

    def test_filter_by_priority(self, client):
        token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, token)
        proj = _create_project(client, token, org["id"])
        _create_task(client, token, org["id"], proj["id"], title="Low", priority="low")
        _create_task(client, token, org["id"], proj["id"], title="High", priority="high")
        r = client.get(
            f"/api/v1/organizations/{org['id']}/projects/{proj['id']}/tasks?priority=high",
            headers=_auth(token),
        )
        assert r.status_code == 200
        assert all(t["priority"] == "high" for t in r.json())

    def test_list_excludes_deleted(self, client):
        owner_token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, owner_token)
        proj = _create_project(client, owner_token, org["id"])
        t1 = _create_task(client, owner_token, org["id"], proj["id"], title="Keep")
        t2 = _create_task(client, owner_token, org["id"], proj["id"], title="Delete")
        client.delete(
            f"/api/v1/organizations/{org['id']}/tasks/{t2['id']}",
            headers=_auth(owner_token),
        )
        r = client.get(
            f"/api/v1/organizations/{org['id']}/projects/{proj['id']}/tasks",
            headers=_auth(owner_token),
        )
        ids = [t["id"] for t in r.json()]
        assert t1["id"] in ids
        assert t2["id"] not in ids

    def test_list_requires_membership(self, client):
        owner_token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, owner_token)
        proj = _create_project(client, owner_token, org["id"])
        outsider_token = _login(client, _register(client, "out@t.com")["email"])
        r = client.get(
            f"/api/v1/organizations/{org['id']}/projects/{proj['id']}/tasks",
            headers=_auth(outsider_token),
        )
        assert r.status_code == 403


# --------------------------------------------------------------------------- #
# GET …/tasks/{task_id} — retrieve                                             #
# --------------------------------------------------------------------------- #


class TestGetTask:
    def test_get_ok(self, client):
        token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, token)
        proj = _create_project(client, token, org["id"])
        task = _create_task(client, token, org["id"], proj["id"])
        r = client.get(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}",
            headers=_auth(token),
        )
        assert r.status_code == 200
        assert r.json()["id"] == task["id"]

    def test_get_not_found(self, client):
        token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, token)
        fake = "00000000-0000-0000-0000-000000000000"
        r = client.get(
            f"/api/v1/organizations/{org['id']}/tasks/{fake}",
            headers=_auth(token),
        )
        assert r.status_code == 404

    def test_get_wrong_org_404(self, client):
        t1 = _login(client, _register(client, "o1@t.com")["email"])
        t2 = _login(client, _register(client, "o2@t.com")["email"])
        org1 = _create_org(client, t1, name="Org1", slug="org1")
        org2 = _create_org(client, t2, name="Org2", slug="org2")
        proj2 = _create_project(client, t2, org2["id"])
        task2 = _create_task(client, t2, org2["id"], proj2["id"])
        r = client.get(
            f"/api/v1/organizations/{org1['id']}/tasks/{task2['id']}",
            headers=_auth(t1),
        )
        assert r.status_code == 404

    def test_get_deleted_task_404(self, client):
        token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, token)
        proj = _create_project(client, token, org["id"])
        task = _create_task(client, token, org["id"], proj["id"])
        client.delete(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}",
            headers=_auth(token),
        )
        r = client.get(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}",
            headers=_auth(token),
        )
        assert r.status_code == 404


# --------------------------------------------------------------------------- #
# PATCH …/tasks/{task_id} — update                                             #
# --------------------------------------------------------------------------- #


class TestUpdateTask:
    def test_update_title(self, client):
        token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, token)
        proj = _create_project(client, token, org["id"])
        task = _create_task(client, token, org["id"], proj["id"])
        r = client.patch(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}",
            json={"title": "Updated"},
            headers=_auth(token),
        )
        assert r.status_code == 200
        assert r.json()["title"] == "Updated"

    def test_update_status(self, client):
        token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, token)
        proj = _create_project(client, token, org["id"])
        task = _create_task(client, token, org["id"], proj["id"])
        r = client.patch(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}",
            json={"status": "done"},
            headers=_auth(token),
        )
        assert r.status_code == 200
        assert r.json()["status"] == "done"

    def test_update_member_can_update(self, client):
        owner_token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, owner_token)
        proj = _create_project(client, owner_token, org["id"])
        task = _create_task(client, owner_token, org["id"], proj["id"])
        member_token = _invite_and_join(client, owner_token, org["id"], "m@t.com")
        r = client.patch(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}",
            json={"title": "Member updated"},
            headers=_auth(member_token),
        )
        assert r.status_code == 200

    def test_update_empty_body_noop(self, client):
        token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, token)
        proj = _create_project(client, token, org["id"])
        task = _create_task(client, token, org["id"], proj["id"], title="Stable")
        r = client.patch(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}",
            json={},
            headers=_auth(token),
        )
        assert r.status_code == 200
        assert r.json()["title"] == "Stable"

    def test_update_not_found(self, client):
        token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, token)
        fake = "00000000-0000-0000-0000-000000000000"
        r = client.patch(
            f"/api/v1/organizations/{org['id']}/tasks/{fake}",
            json={"title": "X"},
            headers=_auth(token),
        )
        assert r.status_code == 404


# --------------------------------------------------------------------------- #
# DELETE …/tasks/{task_id} — soft delete                                       #
# --------------------------------------------------------------------------- #


class TestDeleteTask:
    def test_delete_ok_as_owner(self, client):
        token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, token)
        proj = _create_project(client, token, org["id"])
        task = _create_task(client, token, org["id"], proj["id"])
        r = client.delete(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}",
            headers=_auth(token),
        )
        assert r.status_code == 204

    def test_delete_forbidden_for_member(self, client):
        owner_token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, owner_token)
        proj = _create_project(client, owner_token, org["id"])
        task = _create_task(client, owner_token, org["id"], proj["id"])
        member_token = _invite_and_join(client, owner_token, org["id"], "m@t.com")
        r = client.delete(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}",
            headers=_auth(member_token),
        )
        assert r.status_code == 403

    def test_delete_not_found(self, client):
        token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, token)
        fake = "00000000-0000-0000-0000-000000000000"
        r = client.delete(
            f"/api/v1/organizations/{org['id']}/tasks/{fake}",
            headers=_auth(token),
        )
        assert r.status_code == 404

    def test_soft_delete_hides_task(self, client):
        """Deleted task should not appear in list or get."""
        token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, token)
        proj = _create_project(client, token, org["id"])
        task = _create_task(client, token, org["id"], proj["id"])
        client.delete(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}",
            headers=_auth(token),
        )
        r = client.get(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}",
            headers=_auth(token),
        )
        assert r.status_code == 404


# --------------------------------------------------------------------------- #
# POST …/tasks/{task_id}/labels — attach                                       #
# --------------------------------------------------------------------------- #


class TestAddLabel:
    def test_add_label_creates_and_attaches(self, client):
        token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, token)
        proj = _create_project(client, token, org["id"])
        task = _create_task(client, token, org["id"], proj["id"])
        r = client.post(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}/labels",
            json={"name": "bug"},
            headers=_auth(token),
        )
        assert r.status_code == 200
        labels = r.json()["labels"]
        assert len(labels) == 1
        assert labels[0]["name"] == "bug"

    def test_add_label_with_color(self, client):
        token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, token)
        proj = _create_project(client, token, org["id"])
        task = _create_task(client, token, org["id"], proj["id"])
        r = client.post(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}/labels",
            json={"name": "urgent", "color": "#FF0000"},
            headers=_auth(token),
        )
        assert r.status_code == 200
        assert r.json()["labels"][0]["color"] == "#FF0000"

    def test_add_same_label_twice_is_idempotent(self, client):
        token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, token)
        proj = _create_project(client, token, org["id"])
        task = _create_task(client, token, org["id"], proj["id"])
        for _ in range(2):
            r = client.post(
                f"/api/v1/organizations/{org['id']}/tasks/{task['id']}/labels",
                json={"name": "duplicate"},
                headers=_auth(token),
            )
            assert r.status_code == 200
        assert len(r.json()["labels"]) == 1

    def test_add_multiple_labels(self, client):
        token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, token)
        proj = _create_project(client, token, org["id"])
        task = _create_task(client, token, org["id"], proj["id"])
        for name in ["bug", "feature", "urgent"]:
            client.post(
                f"/api/v1/organizations/{org['id']}/tasks/{task['id']}/labels",
                json={"name": name},
                headers=_auth(token),
            )
        r = client.get(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}",
            headers=_auth(token),
        )
        assert len(r.json()["labels"]) == 3

    def test_add_label_invalid_color_422(self, client):
        token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, token)
        proj = _create_project(client, token, org["id"])
        task = _create_task(client, token, org["id"], proj["id"])
        r = client.post(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}/labels",
            json={"name": "bad", "color": "red"},
            headers=_auth(token),
        )
        assert r.status_code == 422


# --------------------------------------------------------------------------- #
# DELETE …/tasks/{task_id}/labels/{label_name} — detach                        #
# --------------------------------------------------------------------------- #


class TestRemoveLabel:
    def test_remove_label_ok(self, client):
        token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, token)
        proj = _create_project(client, token, org["id"])
        task = _create_task(client, token, org["id"], proj["id"])
        client.post(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}/labels",
            json={"name": "removeme"},
            headers=_auth(token),
        )
        r = client.delete(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}/labels/removeme",
            headers=_auth(token),
        )
        assert r.status_code == 204

        # Confirm gone
        r = client.get(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}",
            headers=_auth(token),
        )
        assert r.json()["labels"] == []

    def test_remove_label_not_found(self, client):
        token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, token)
        proj = _create_project(client, token, org["id"])
        task = _create_task(client, token, org["id"], proj["id"])
        r = client.delete(
            f"/api/v1/organizations/{org['id']}/tasks/{task['id']}/labels/nonexistent",
            headers=_auth(token),
        )
        assert r.status_code == 404

    def test_remove_label_not_attached(self, client):
        token = _login(client, _register(client, "o@t.com")["email"])
        org = _create_org(client, token)
        proj = _create_project(client, token, org["id"])
        t1 = _create_task(client, token, org["id"], proj["id"], title="T1")
        t2 = _create_task(client, token, org["id"], proj["id"], title="T2")
        # Add label to t2 only
        client.post(
            f"/api/v1/organizations/{org['id']}/tasks/{t2['id']}/labels",
            json={"name": "onlyt2"},
            headers=_auth(token),
        )
        # Try to remove from t1
        r = client.delete(
            f"/api/v1/organizations/{org['id']}/tasks/{t1['id']}/labels/onlyt2",
            headers=_auth(token),
        )
        assert r.status_code == 404
