# Changelog

All notable changes to Tenantrix will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- M7 — Audit logging
- M8 — Integration tests + CI/CD
- M9 — Hardening, rate limiting, idempotency, security review

---

## [0.6.0] — 2026-03-05 — M6: Comments

### Added
- `app/schemas/comment.py` — `CommentCreateRequest`, `CommentUpdateRequest`, `CommentOut` (Pydantic v2)
- `app/api/v1/comments.py` — 4 endpoints:
  - `POST   /api/v1/organizations/{org_id}/tasks/{task_id}/comments` — add comment to task (MEMBER+)
  - `GET    /api/v1/organizations/{org_id}/tasks/{task_id}/comments` — list active comments, oldest-first (MEMBER+)
  - `PATCH  /api/v1/organizations/{org_id}/comments/{comment_id}` — edit body (author or ADMIN+)
  - `DELETE /api/v1/organizations/{org_id}/comments/{comment_id}` — soft delete (author or ADMIN+)
- `tests/test_comments.py` — 23 tests covering all endpoints and access-control edge cases

### Implementation Notes
- Soft delete: `deleted_at` timestamp — hidden from list, subsequent operations return 404
- Edit/delete guard: author **or** ADMIN/OWNER may modify; plain MEMBER cannot touch others' comments
- `comment.author_user_id` sourced from the authenticated membership, not the request body
- Fixed pre-existing `test_login_success` hard-coded `expires_in` → now reads from `settings.ACCESS_TOKEN_EXPIRE_MINUTES`

---

## [0.5.0] — 2026-03-05 — M5: Task Management

### Added
- `app/schemas/task.py` — `TaskCreateRequest`, `TaskUpdateRequest`, `TaskOut`, `LabelCreateRequest`, `LabelOut` (Pydantic v2)
- `app/api/v1/tasks.py` — 7 endpoints:
  - `POST   /api/v1/organizations/{org_id}/projects/{project_id}/tasks` — create task (MEMBER+)
  - `GET    /api/v1/organizations/{org_id}/projects/{project_id}/tasks` — list tasks with filters: `status`, `priority`, `assignee_user_id` (MEMBER+)
  - `GET    /api/v1/organizations/{org_id}/tasks/{task_id}` — retrieve task (MEMBER+)
  - `PATCH  /api/v1/organizations/{org_id}/tasks/{task_id}` — update task fields (MEMBER+)
  - `DELETE /api/v1/organizations/{org_id}/tasks/{task_id}` — soft delete via `deleted_at` (ADMIN+)
  - `POST   /api/v1/organizations/{org_id}/tasks/{task_id}/labels` — upsert label by name + attach to task (MEMBER+)
  - `DELETE /api/v1/organizations/{org_id}/tasks/{task_id}/labels/{label_name}` — detach label from task (MEMBER+)
- `tests/test_tasks.py` — 35 tests covering all endpoints and edge cases

### Implementation Notes
- Soft delete: `deleted_at` timestamp; `NULL` = active; hidden from all reads
- Label upsert: get-or-create label by `(org_id, name)`, idempotent attachment
- Assignee validation: must be an active org member
- `db.expire_all()` after commit ensures fresh `selectinload` of `task_labels → label`
- `# noqa: B008` added to `organizations.py` `Depends(get_db)` lines (pre-existing omission)

---

## [0.2.0] — 2026-03-03 — M2: Authentication

### Added
- `app/core/security.py` — bcrypt password hashing, JWT access token create/verify, opaque refresh token generation (SHA-256 hashed in DB)
- `app/schemas/auth.py` — Pydantic v2 request/response schemas: `RegisterRequest`, `LoginRequest`, `RefreshRequest`, `LogoutRequest`, `UserOut`, `TokenPair`, `AccessTokenOut`, `MessageOut`
- `app/api/deps.py` — `get_current_user` FastAPI dependency + `CurrentUser` type alias
- `app/api/v1/auth.py` — 5 auth endpoints:
  - `POST /api/v1/auth/register` — create account (409 on duplicate email, 422 on weak password)
  - `POST /api/v1/auth/login` — authenticate, returns JWT access token (15 min) + opaque refresh token (7 days)
  - `POST /api/v1/auth/refresh` — rotate refresh token, reuse detection wipes entire family
  - `POST /api/v1/auth/logout` — revoke refresh token (idempotent, always 200)
  - `GET /api/v1/auth/me` — return current user (requires Bearer JWT)
- `email-validator>=2.0.0` added to dependencies (required for `pydantic.EmailStr`)
- `tests/test_auth.py` — 22 new tests covering all endpoints and edge cases

### Security
- Refresh token rotation: each use issues a new token, old one is immediately revoked
- Reuse detection: presenting a revoked token triggers immediate invalidation of the entire token family
- Passwords stored as bcrypt hashes; raw tokens never persisted (SHA-256 hash only)
- Timing-safe email comparison (no user enumeration on login)
- JWT `type: access` claim validation to prevent refresh tokens being used as access tokens

### Tests
- **39/39 passing** (was 17/17 before M2)
- Per-test DB isolation via table truncation (`TRUNCATE ... CASCADE`) in `conftest.py`

---

## [0.1.0] — TBD

### Added
- Initial project structure
- `README.md` — project overview, quick start, API endpoint table, RBAC matrix
- `ARCHITECTURE.md` — system design, data model, auth flows, RBAC, security checklist
- `API.md` — full API reference with request/response examples for all 30+ endpoints
- `CHANGELOG.md` — this file

### Tech Stack Finalized
- FastAPI 0.135.1
- SQLAlchemy 2.0.48 (sync)
- PostgreSQL 16
- Pydantic v2
- PyJWT + passlib[bcrypt]
- slowapi (rate limiting)
- Alembic (migrations)
- pytest + HTTPX (testing)
- Ruff + Black (linting/formatting)
- Docker + Docker Compose
- GitHub Actions (CI/CD)

### Key Design Decisions
- **Multi-tenancy**: Shared DB, shared schema with `org_id` on all tenant-scoped tables
- **Refresh tokens**: Opaque random tokens (SHA-256 hashed in DB) with rotation + reuse detection
- **JWT library**: PyJWT (not python-jose — stagnant, CVEs)
- **RBAC roles**: OWNER > ADMIN > MEMBER > VIEWER (4-tier, org-level only in v1)
- **Soft deletes**: `deleted_at` timestamp pattern on tasks and comments
- **Idempotency**: Optional `Idempotency-Key` header, dependency-based enforcement
- **Invite token delivery**: Returned in API response body (v1 — no email sending yet)
- **Project-level roles**: Skipped in v1, planned for v2

---

[Unreleased]: https://github.com/DevaVirathan/Tenantrix/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/DevaVirathan/Tenantrix/releases/tag/v0.1.0
