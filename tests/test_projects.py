"""Tests for M4 — project management endpoints."""

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
    """Invite user and have them accept the invite, returning their token."""
    _register(client, email)
    member_token = _login(client, email)

    # Invite
    r = client.post(
        f"/api/v1/organizations/{org_id}/invites",
        json={"email": email, "role": role},
        headers=_auth(owner_token),
    )
    assert r.status_code == 201, r.text
    invite_token = r.json()["token"]

    # Accept
    r = client.post(f"/api/v1/organizations/invites/accept/{invite_token}", headers=_auth(member_token))
    assert r.status_code == 200, r.text

    return member_token


def _create_project(client, token, org_id, name="Alpha", description=None, status="active"):
    payload: dict = {"name": name, "status": status}
    if description:
        payload["description"] = description
    r = client.post(f"/api/v1/organizations/{org_id}/projects", json=payload, headers=_auth(token))
    assert r.status_code == 201, r.text
    return r.json()


# --------------------------------------------------------------------------- #
# POST /organizations/{org_id}/projects — create                                #
# --------------------------------------------------------------------------- #


class TestCreateProject:
    def test_create_ok_as_owner(self, client):
        token = _login(client, _register(client, "owner@test.com")["email"])
        org = _create_org(client, token)
        data = _create_project(client, token, org["id"])
        assert data["name"] == "Alpha"
        assert data["organization_id"] == org["id"]
        assert data["status"] == "active"
        assert "id" in data

    def test_create_ok_as_member(self, client):
        owner_token = _login(client, _register(client, "owner@test.com")["email"])
        org = _create_org(client, owner_token)
        member_token = _invite_and_join(client, owner_token, org["id"], "member@test.com")
        data = _create_project(client, member_token, org["id"], name="Beta")
        assert data["name"] == "Beta"

    def test_create_with_description(self, client):
        token = _login(client, _register(client, "owner@test.com")["email"])
        org = _create_org(client, token)
        data = _create_project(client, token, org["id"], description="A great project")
        assert data["description"] == "A great project"

    def test_create_with_archived_status(self, client):
        token = _login(client, _register(client, "owner@test.com")["email"])
        org = _create_org(client, token)
        data = _create_project(client, token, org["id"], status="archived")
        assert data["status"] == "archived"

    def test_create_requires_auth(self, client):
        token = _login(client, _register(client, "owner@test.com")["email"])
        org = _create_org(client, token)
        r = client.post(f"/api/v1/organizations/{org['id']}/projects", json={"name": "X"})
        assert r.status_code in (401, 403)

    def test_create_non_member_forbidden(self, client):
        owner_token = _login(client, _register(client, "owner@test.com")["email"])
        org = _create_org(client, owner_token)
        outsider_token = _login(client, _register(client, "outsider@test.com")["email"])
        r = client.post(
            f"/api/v1/organizations/{org['id']}/projects",
            json={"name": "X"},
            headers=_auth(outsider_token),
        )
        assert r.status_code == 403

    def test_create_missing_name(self, client):
        token = _login(client, _register(client, "owner@test.com")["email"])
        org = _create_org(client, token)
        r = client.post(
            f"/api/v1/organizations/{org['id']}/projects",
            json={},
            headers=_auth(token),
        )
        assert r.status_code == 422

    def test_create_name_too_long(self, client):
        token = _login(client, _register(client, "owner@test.com")["email"])
        org = _create_org(client, token)
        r = client.post(
            f"/api/v1/organizations/{org['id']}/projects",
            json={"name": "x" * 256},
            headers=_auth(token),
        )
        assert r.status_code == 422

    def test_create_org_not_found(self, client):
        token = _login(client, _register(client, "owner@test.com")["email"])
        fake_id = "00000000-0000-0000-0000-000000000000"
        r = client.post(
            f"/api/v1/organizations/{fake_id}/projects",
            json={"name": "X"},
            headers=_auth(token),
        )
        assert r.status_code == 404


# --------------------------------------------------------------------------- #
# GET /organizations/{org_id}/projects — list                                   #
# --------------------------------------------------------------------------- #


class TestListProjects:
    def test_list_empty(self, client):
        token = _login(client, _register(client, "owner@test.com")["email"])
        org = _create_org(client, token)
        r = client.get(f"/api/v1/organizations/{org['id']}/projects", headers=_auth(token))
        assert r.status_code == 200
        assert r.json() == []

    def test_list_multiple(self, client):
        token = _login(client, _register(client, "owner@test.com")["email"])
        org = _create_org(client, token)
        _create_project(client, token, org["id"], name="Alpha")
        _create_project(client, token, org["id"], name="Beta")
        r = client.get(f"/api/v1/organizations/{org['id']}/projects", headers=_auth(token))
        assert r.status_code == 200
        names = {p["name"] for p in r.json()}
        assert names == {"Alpha", "Beta"}

    def test_list_requires_membership(self, client):
        owner_token = _login(client, _register(client, "owner@test.com")["email"])
        org = _create_org(client, owner_token)
        _create_project(client, owner_token, org["id"])
        outsider_token = _login(client, _register(client, "outsider@test.com")["email"])
        r = client.get(f"/api/v1/organizations/{org['id']}/projects", headers=_auth(outsider_token))
        assert r.status_code == 403

    def test_list_requires_auth(self, client):
        token = _login(client, _register(client, "owner@test.com")["email"])
        org = _create_org(client, token)
        r = client.get(f"/api/v1/organizations/{org['id']}/projects")
        assert r.status_code in (401, 403)

    def test_list_only_own_org_projects(self, client):
        """Projects from another org should not appear in the list."""
        t1 = _login(client, _register(client, "owner1@test.com")["email"])
        t2 = _login(client, _register(client, "owner2@test.com")["email"])
        org1 = _create_org(client, t1, name="Org1", slug="org1")
        org2 = _create_org(client, t2, name="Org2", slug="org2")
        _create_project(client, t1, org1["id"], name="OrgOneProject")
        _create_project(client, t2, org2["id"], name="OrgTwoProject")
        r = client.get(f"/api/v1/organizations/{org1['id']}/projects", headers=_auth(t1))
        assert r.status_code == 200
        names = [p["name"] for p in r.json()]
        assert "OrgOneProject" in names
        assert "OrgTwoProject" not in names


# --------------------------------------------------------------------------- #
# GET /organizations/{org_id}/projects/{project_id} — retrieve                 #
# --------------------------------------------------------------------------- #


class TestGetProject:
    def test_get_ok(self, client):
        token = _login(client, _register(client, "owner@test.com")["email"])
        org = _create_org(client, token)
        project = _create_project(client, token, org["id"])
        r = client.get(
            f"/api/v1/organizations/{org['id']}/projects/{project['id']}",
            headers=_auth(token),
        )
        assert r.status_code == 200
        assert r.json()["id"] == project["id"]

    def test_get_not_found(self, client):
        token = _login(client, _register(client, "owner@test.com")["email"])
        org = _create_org(client, token)
        fake_id = "00000000-0000-0000-0000-000000000000"
        r = client.get(
            f"/api/v1/organizations/{org['id']}/projects/{fake_id}",
            headers=_auth(token),
        )
        assert r.status_code == 404

    def test_get_wrong_org_returns_404(self, client):
        """A project in org2 should be invisible via org1's path."""
        t1 = _login(client, _register(client, "owner1@test.com")["email"])
        t2 = _login(client, _register(client, "owner2@test.com")["email"])
        org1 = _create_org(client, t1, name="Org1", slug="org1")
        org2 = _create_org(client, t2, name="Org2", slug="org2")
        project2 = _create_project(client, t2, org2["id"], name="Secret")
        r = client.get(
            f"/api/v1/organizations/{org1['id']}/projects/{project2['id']}",
            headers=_auth(t1),
        )
        assert r.status_code == 404

    def test_get_requires_membership(self, client):
        owner_token = _login(client, _register(client, "owner@test.com")["email"])
        org = _create_org(client, owner_token)
        project = _create_project(client, owner_token, org["id"])
        outsider_token = _login(client, _register(client, "out@test.com")["email"])
        r = client.get(
            f"/api/v1/organizations/{org['id']}/projects/{project['id']}",
            headers=_auth(outsider_token),
        )
        assert r.status_code == 403


# --------------------------------------------------------------------------- #
# PATCH /organizations/{org_id}/projects/{project_id} — update                 #
# --------------------------------------------------------------------------- #


class TestUpdateProject:
    def test_update_name_as_admin(self, client):
        owner_token = _login(client, _register(client, "owner@test.com")["email"])
        org = _create_org(client, owner_token)
        project = _create_project(client, owner_token, org["id"])
        r = client.patch(
            f"/api/v1/organizations/{org['id']}/projects/{project['id']}",
            json={"name": "Renamed"},
            headers=_auth(owner_token),
        )
        assert r.status_code == 200
        assert r.json()["name"] == "Renamed"

    def test_update_status_to_archived(self, client):
        token = _login(client, _register(client, "owner@test.com")["email"])
        org = _create_org(client, token)
        project = _create_project(client, token, org["id"])
        r = client.patch(
            f"/api/v1/organizations/{org['id']}/projects/{project['id']}",
            json={"status": "archived"},
            headers=_auth(token),
        )
        assert r.status_code == 200
        assert r.json()["status"] == "archived"

    def test_update_description(self, client):
        token = _login(client, _register(client, "owner@test.com")["email"])
        org = _create_org(client, token)
        project = _create_project(client, token, org["id"])
        r = client.patch(
            f"/api/v1/organizations/{org['id']}/projects/{project['id']}",
            json={"description": "Updated description"},
            headers=_auth(token),
        )
        assert r.status_code == 200
        assert r.json()["description"] == "Updated description"

    def test_update_forbidden_for_member(self, client):
        owner_token = _login(client, _register(client, "owner@test.com")["email"])
        org = _create_org(client, owner_token)
        project = _create_project(client, owner_token, org["id"])
        member_token = _invite_and_join(client, owner_token, org["id"], "member@test.com")
        r = client.patch(
            f"/api/v1/organizations/{org['id']}/projects/{project['id']}",
            json={"name": "Hacked"},
            headers=_auth(member_token),
        )
        assert r.status_code == 403

    def test_update_not_found(self, client):
        token = _login(client, _register(client, "owner@test.com")["email"])
        org = _create_org(client, token)
        fake_id = "00000000-0000-0000-0000-000000000000"
        r = client.patch(
            f"/api/v1/organizations/{org['id']}/projects/{fake_id}",
            json={"name": "X"},
            headers=_auth(token),
        )
        assert r.status_code == 404

    def test_update_empty_body_is_noop(self, client):
        """PATCH with no fields should not error and return unchanged project."""
        token = _login(client, _register(client, "owner@test.com")["email"])
        org = _create_org(client, token)
        project = _create_project(client, token, org["id"], name="Unchanged")
        r = client.patch(
            f"/api/v1/organizations/{org['id']}/projects/{project['id']}",
            json={},
            headers=_auth(token),
        )
        assert r.status_code == 200
        assert r.json()["name"] == "Unchanged"


# --------------------------------------------------------------------------- #
# DELETE /organizations/{org_id}/projects/{project_id} — delete                #
# --------------------------------------------------------------------------- #


class TestDeleteProject:
    def test_delete_ok_as_owner(self, client):
        token = _login(client, _register(client, "owner@test.com")["email"])
        org = _create_org(client, token)
        project = _create_project(client, token, org["id"])
        r = client.delete(
            f"/api/v1/organizations/{org['id']}/projects/{project['id']}",
            headers=_auth(token),
        )
        assert r.status_code == 204

        # Confirm it's gone
        r = client.get(
            f"/api/v1/organizations/{org['id']}/projects/{project['id']}",
            headers=_auth(token),
        )
        assert r.status_code == 404

    def test_delete_forbidden_for_member(self, client):
        owner_token = _login(client, _register(client, "owner@test.com")["email"])
        org = _create_org(client, owner_token)
        project = _create_project(client, owner_token, org["id"])
        member_token = _invite_and_join(client, owner_token, org["id"], "member@test.com")
        r = client.delete(
            f"/api/v1/organizations/{org['id']}/projects/{project['id']}",
            headers=_auth(member_token),
        )
        assert r.status_code == 403

    def test_delete_not_found(self, client):
        token = _login(client, _register(client, "owner@test.com")["email"])
        org = _create_org(client, token)
        fake_id = "00000000-0000-0000-0000-000000000000"
        r = client.delete(
            f"/api/v1/organizations/{org['id']}/projects/{fake_id}",
            headers=_auth(token),
        )
        assert r.status_code == 404

    def test_delete_not_in_list_after(self, client):
        token = _login(client, _register(client, "owner@test.com")["email"])
        org = _create_org(client, token)
        p1 = _create_project(client, token, org["id"], name="Keep")
        p2 = _create_project(client, token, org["id"], name="Remove")

        client.delete(
            f"/api/v1/organizations/{org['id']}/projects/{p2['id']}",
            headers=_auth(token),
        )

        r = client.get(f"/api/v1/organizations/{org['id']}/projects", headers=_auth(token))
        ids = [p["id"] for p in r.json()]
        assert p1["id"] in ids
        assert p2["id"] not in ids
