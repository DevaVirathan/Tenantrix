"""Tests for M3 — organization management endpoints."""

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
    """Return the access token."""
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_org(client, token, name="Acme", slug="acme", description=None):
    payload = {"name": name, "slug": slug}
    if description:
        payload["description"] = description
    r = client.post("/api/v1/organizations", json=payload, headers=_auth(token))
    assert r.status_code == 201, r.text
    return r.json()


# --------------------------------------------------------------------------- #
# POST /organizations — create                                                  #
# --------------------------------------------------------------------------- #


class TestCreateOrg:
    def test_create_ok(self, client):
        token = _login(client, _register(client, "owner@test.com")["email"])
        data = _create_org(client, token, name="Acme Corp", slug="acme-corp")
        assert data["slug"] == "acme-corp"
        assert data["name"] == "Acme Corp"
        assert "id" in data

    def test_create_requires_auth(self, client):
        r = client.post("/api/v1/organizations", json={"name": "X", "slug": "x"})
        assert r.status_code in (401, 403)

    def test_duplicate_slug_returns_409(self, client):
        t = _login(client, _register(client, "a@test.com")["email"])
        _create_org(client, t, slug="my-org")
        r = client.post(
            "/api/v1/organizations", json={"name": "Other", "slug": "my-org"}, headers=_auth(t)
        )
        assert r.status_code == 409

    def test_invalid_slug_rejected(self, client):
        t = _login(client, _register(client, "b@test.com")["email"])
        r = client.post(
            "/api/v1/organizations",
            json={"name": "Bad", "slug": "UPPER_CASE"},
            headers=_auth(t),
        )
        assert r.status_code == 422

    def test_creator_becomes_owner(self, client):
        t = _login(client, _register(client, "c@test.com")["email"])
        org = _create_org(client, t, slug="owner-check")
        members = client.get(f"/api/v1/organizations/{org['id']}/members", headers=_auth(t)).json()
        assert len(members) == 1
        assert members[0]["role"] == "owner"


# --------------------------------------------------------------------------- #
# GET /organizations/{org_id}                                                  #
# --------------------------------------------------------------------------- #


class TestGetOrg:
    def test_get_ok(self, client):
        t = _login(client, _register(client, "get@test.com")["email"])
        org = _create_org(client, t, slug="get-org")
        r = client.get(f"/api/v1/organizations/{org['id']}", headers=_auth(t))
        assert r.status_code == 200
        assert r.json()["slug"] == "get-org"

    def test_non_member_gets_403(self, client):
        owner_t = _login(client, _register(client, "owner2@test.com")["email"])
        stranger_t = _login(client, _register(client, "stranger@test.com")["email"])
        org = _create_org(client, owner_t, slug="private-org")
        r = client.get(f"/api/v1/organizations/{org['id']}", headers=_auth(stranger_t))
        assert r.status_code == 403

    def test_unknown_org_returns_404(self, client):
        t = _login(client, _register(client, "nobody@test.com")["email"])
        import uuid

        r = client.get(f"/api/v1/organizations/{uuid.uuid4()}", headers=_auth(t))
        assert r.status_code == 404


# --------------------------------------------------------------------------- #
# GET /organizations/{org_id}/members                                          #
# --------------------------------------------------------------------------- #


class TestListMembers:
    def test_lists_only_active(self, client):
        t = _login(client, _register(client, "lm@test.com")["email"])
        org = _create_org(client, t, slug="list-members")
        members = client.get(f"/api/v1/organizations/{org['id']}/members", headers=_auth(t)).json()
        assert len(members) == 1
        assert members[0]["status"] == "active"


# --------------------------------------------------------------------------- #
# POST /organizations/{org_id}/invites                                         #
# --------------------------------------------------------------------------- #


class TestInvite:
    def test_admin_can_invite(self, client):
        owner_t = _login(client, _register(client, "owner3@test.com")["email"])
        _register(client, "invitee@test.com")
        org = _create_org(client, owner_t, slug="invite-org")
        r = client.post(
            f"/api/v1/organizations/{org['id']}/invites",
            json={"email": "invitee@test.com", "role": "member"},
            headers=_auth(owner_t),
        )
        assert r.status_code == 201
        assert r.json()["email"] == "invitee@test.com"
        assert "token" in r.json()

    def test_member_cannot_invite(self, client):
        owner_t = _login(client, _register(client, "owner4@test.com")["email"])
        mem_email = "mem@test.com"
        mem_t = _login(client, _register(client, mem_email)["email"])
        org = _create_org(client, owner_t, slug="invite-rbac")

        # Get owner to invite mem first, then accept
        inv = client.post(
            f"/api/v1/organizations/{org['id']}/invites",
            json={"email": mem_email, "role": "member"},
            headers=_auth(owner_t),
        ).json()
        client.post(
            f"/api/v1/organizations/invites/accept/{inv['token']}",
            headers=_auth(mem_t),
        )

        # Now member tries to invite someone else
        r = client.post(
            f"/api/v1/organizations/{org['id']}/invites",
            json={"email": "other@test.com", "role": "member"},
            headers=_auth(mem_t),
        )
        assert r.status_code == 403

    def test_re_invite_replaces_old_invite(self, client):
        owner_t = _login(client, _register(client, "owner5@test.com")["email"])
        org = _create_org(client, owner_t, slug="reinvite-org")
        _register(client, "reinvitee@test.com")

        inv1 = client.post(
            f"/api/v1/organizations/{org['id']}/invites",
            json={"email": "reinvitee@test.com", "role": "member"},
            headers=_auth(owner_t),
        ).json()
        inv2 = client.post(
            f"/api/v1/organizations/{org['id']}/invites",
            json={"email": "reinvitee@test.com", "role": "admin"},
            headers=_auth(owner_t),
        ).json()

        # Old token should be gone (accept should fail)
        assert inv1["token"] != inv2["token"]

    def test_cannot_invite_existing_member(self, client):
        owner_t = _login(client, _register(client, "owner6@test.com")["email"])
        org = _create_org(client, owner_t, slug="dup-invite")

        # Invite owner themselves
        r = client.post(
            f"/api/v1/organizations/{org['id']}/invites",
            json={"email": "owner6@test.com", "role": "member"},
            headers=_auth(owner_t),
        )
        assert r.status_code == 409


# --------------------------------------------------------------------------- #
# POST /organizations/invites/accept/{token}                                   #
# --------------------------------------------------------------------------- #


class TestAcceptInvite:
    def _setup(self, client):
        owner_t = _login(client, _register(client, "oi-owner@test.com")["email"])
        invitee = _register(client, "oi-invitee@test.com")
        invitee_t = _login(client, invitee["email"])
        org = _create_org(client, owner_t, slug="accept-org")
        inv = client.post(
            f"/api/v1/organizations/{org['id']}/invites",
            json={"email": "oi-invitee@test.com", "role": "member"},
            headers=_auth(owner_t),
        ).json()
        return org, inv, invitee_t, owner_t

    def test_accept_ok(self, client):
        org, inv, invitee_t, _ = self._setup(client)
        r = client.post(
            f"/api/v1/organizations/invites/accept/{inv['token']}",
            headers=_auth(invitee_t),
        )
        assert r.status_code == 200
        assert r.json()["id"] == org["id"]

    def test_accept_adds_membership(self, client):
        org, inv, invitee_t, owner_t = self._setup(client)
        client.post(
            f"/api/v1/organizations/invites/accept/{inv['token']}",
            headers=_auth(invitee_t),
        )
        members = client.get(
            f"/api/v1/organizations/{org['id']}/members", headers=_auth(owner_t)
        ).json()
        assert len(members) == 2

    def test_double_accept_returns_409(self, client):
        _, inv, invitee_t, _ = self._setup(client)
        client.post(
            f"/api/v1/organizations/invites/accept/{inv['token']}",
            headers=_auth(invitee_t),
        )
        r = client.post(
            f"/api/v1/organizations/invites/accept/{inv['token']}",
            headers=_auth(invitee_t),
        )
        assert r.status_code == 409

    def test_wrong_user_email_rejected(self, client):
        _, inv, _, _ = self._setup(client)
        wrong_t = _login(client, _register(client, "wrong@test.com")["email"])
        r = client.post(
            f"/api/v1/organizations/invites/accept/{inv['token']}",
            headers=_auth(wrong_t),
        )
        assert r.status_code == 403

    def test_unknown_token_returns_404(self, client):
        t = _login(client, _register(client, "nobody2@test.com")["email"])
        r = client.post(
            "/api/v1/organizations/invites/accept/bad-token-xyz",
            headers=_auth(t),
        )
        assert r.status_code == 404


# --------------------------------------------------------------------------- #
# PATCH /organizations/{org_id}/members/{user_id}/role                        #
# --------------------------------------------------------------------------- #


class TestChangeRole:
    def _setup_with_member(self, client, owner_email, member_email, slug):
        owner_t = _login(client, _register(client, owner_email)["email"])
        member_info = _register(client, member_email)
        member_t = _login(client, member_info["email"])
        org = _create_org(client, owner_t, slug=slug)

        # Invite + accept
        inv = client.post(
            f"/api/v1/organizations/{org['id']}/invites",
            json={"email": member_email, "role": "member"},
            headers=_auth(owner_t),
        ).json()
        client.post(
            f"/api/v1/organizations/invites/accept/{inv['token']}",
            headers=_auth(member_t),
        )

        # Get member's user id
        members = client.get(
            f"/api/v1/organizations/{org['id']}/members", headers=_auth(owner_t)
        ).json()
        member_uid = next(m["user_id"] for m in members if m["role"] == "member")
        return org, owner_t, member_t, member_uid

    def test_owner_can_promote_to_admin(self, client):
        org, owner_t, _, member_uid = self._setup_with_member(
            client, "cr-owner@test.com", "cr-mem@test.com", "cr-org"
        )
        r = client.patch(
            f"/api/v1/organizations/{org['id']}/members/{member_uid}/role",
            json={"role": "admin"},
            headers=_auth(owner_t),
        )
        assert r.status_code == 200
        assert r.json()["role"] == "admin"

    def test_member_cannot_change_role(self, client):
        org, _owner_t, member_t, member_uid = self._setup_with_member(
            client, "cr-owner2@test.com", "cr-mem2@test.com", "cr-org2"
        )
        r = client.patch(
            f"/api/v1/organizations/{org['id']}/members/{member_uid}/role",
            json={"role": "admin"},
            headers=_auth(member_t),
        )
        assert r.status_code == 403

    def test_cannot_change_own_role(self, client):
        owner_t = _login(client, _register(client, "self-role@test.com")["email"])
        org = _create_org(client, owner_t, slug="self-role-org")
        me = client.get("/api/v1/auth/me", headers=_auth(owner_t)).json()
        r = client.patch(
            f"/api/v1/organizations/{org['id']}/members/{me['id']}/role",
            json={"role": "admin"},
            headers=_auth(owner_t),
        )
        assert r.status_code == 400


# --------------------------------------------------------------------------- #
# DELETE /organizations/{org_id}/members/{user_id}                            #
# --------------------------------------------------------------------------- #


class TestRemoveMember:
    def test_owner_can_remove_member(self, client):
        owner_t = _login(client, _register(client, "rm-owner@test.com")["email"])
        mem_email = "rm-mem@test.com"
        mem_t = _login(client, _register(client, mem_email)["email"])
        org = _create_org(client, owner_t, slug="rm-org")

        inv = client.post(
            f"/api/v1/organizations/{org['id']}/invites",
            json={"email": mem_email, "role": "member"},
            headers=_auth(owner_t),
        ).json()
        client.post(
            f"/api/v1/organizations/invites/accept/{inv['token']}",
            headers=_auth(mem_t),
        )

        members = client.get(
            f"/api/v1/organizations/{org['id']}/members", headers=_auth(owner_t)
        ).json()
        member_uid = next(m["user_id"] for m in members if m["role"] == "member")

        r = client.delete(
            f"/api/v1/organizations/{org['id']}/members/{member_uid}",
            headers=_auth(owner_t),
        )
        assert r.status_code == 204

        members_after = client.get(
            f"/api/v1/organizations/{org['id']}/members", headers=_auth(owner_t)
        ).json()
        assert len(members_after) == 1

    def test_cannot_remove_self(self, client):
        owner_t = _login(client, _register(client, "rm-self@test.com")["email"])
        org = _create_org(client, owner_t, slug="rm-self-org")
        me = client.get("/api/v1/auth/me", headers=_auth(owner_t)).json()
        r = client.delete(
            f"/api/v1/organizations/{org['id']}/members/{me['id']}",
            headers=_auth(owner_t),
        )
        assert r.status_code == 400

    def test_member_cannot_remove_others(self, client):
        owner_t = _login(client, _register(client, "rm-owner2@test.com")["email"])
        m1_email = "rm-m1@test.com"
        m2_email = "rm-m2@test.com"
        m1_t = _login(client, _register(client, m1_email)["email"])
        m2_t = _login(client, _register(client, m2_email)["email"])
        org = _create_org(client, owner_t, slug="rm-mem-perm")

        for email, tok in [(m1_email, m1_t), (m2_email, m2_t)]:
            inv = client.post(
                f"/api/v1/organizations/{org['id']}/invites",
                json={"email": email, "role": "member"},
                headers=_auth(owner_t),
            ).json()
            client.post(
                f"/api/v1/organizations/invites/accept/{inv['token']}",
                headers=_auth(tok),
            )

        members = client.get(
            f"/api/v1/organizations/{org['id']}/members", headers=_auth(owner_t)
        ).json()
        m2_uid = next(
            m["user_id"]
            for m in members
            if m["user_id"] != client.get("/api/v1/auth/me", headers=_auth(m1_t)).json()["id"]
            and m["role"] == "member"
        )

        r = client.delete(
            f"/api/v1/organizations/{org['id']}/members/{m2_uid}",
            headers=_auth(m1_t),
        )
        assert r.status_code == 403
