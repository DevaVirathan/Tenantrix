# Changelog

All notable changes to Tenantrix will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- M10 — Idempotency keys (full middleware enforcement on all POST mutations)

---

## [Unreleased] — Refactor: Domain-Layered Architecture

### Changed
- **Project structure** reorganised from flat layout to domain-driven layered architecture,
  matching the `training10x-backend-course-module` pattern.
- **Models** moved from `app/models/` to `app/db/models/` (canonical location);
  old paths retained as compatibility shims (`from app.db.models.X import *`).
- **Endpoint logic** moved from `app/api/v1/*.py` into per-domain routers:
  `app/routers/{auth,organizations,projects,tasks,comments,audit_logs,health}/router.py`.
- **Schemas** moved from `app/schemas/*.py` into per-domain schema modules:
  `app/routers/{domain}/schemas/{domain}_schemas.py`;
  old paths retained as compatibility shims.
- **Service layer** introduced per domain:
  `app/routers/{domain}/services/{domain}_service.py`
  (extracted from inline endpoint logic).
- **Repository layer** introduced per domain:
  `app/routers/{domain}/repositories/{domain}_repo.py`
  (all DB queries encapsulated).
- New top-level router aggregator: `app/routers/setup_router.py` (replaces `app/api/v1/router.py`).
- `app/main.py` updated to import from `app.routers.setup_router`.
- `app/api/deps.py`, `app/services/audit.py`, `app/services/idempotency.py`,
  and `alembic/env.py` updated to use new canonical `app.db.models.*` import paths.

### No Breaking Changes
- All old import paths (`app.models.*`, `app.schemas.*`, `app.api.v1.*`) continue to work
  via compatibility shims — zero changes required in tests or external consumers.
- 199/199 tests pass after restructure.

---

## [0.9.0] — 2026-03-05 — M9: Security Review

### Added
- `app/middleware/security_headers.py` — `SecurityHeadersMiddleware`:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy: geolocation=(), microphone=(), camera=()`
  - `Strict-Transport-Security` (production only)
- `app/core/limiter.py` — extracted global `Limiter` instance (breaks circular import)
- Per-route rate limits on auth endpoints: `/register` 10/min, `/login` 10/min, `/refresh` 20/min
- Rate limiting disabled in `ENVIRONMENT=test` (`enabled=False`) to prevent test flakiness
- Stronger password strength validator in `RegisterRequest`:
  - Requires: uppercase, lowercase, digit, special character
  - Replaces old letters+numbers-only check

### Changed
- `app/schemas/auth.py` — `password_strength` validator replaces `password_not_too_simple`
- `tests/test_auth.py` — default test password updated to `"Secret@123"` (satisfies new rules)
- `.github/workflows/ci.yml` — CI now triggers on `feat/**` branches; coverage threshold raised to 85%

---

## [0.8.0] — 2026-03-05 — M8: Production Hardening

### Added
- `app/middleware/request_id.py` — `RequestIDMiddleware`:
  - Accepts client-supplied `X-Request-ID` (validates UUID) or generates a fresh UUID4
  - Echoes resolved ID in `X-Request-ID` response header
  - Stores on `request.state.request_id` for logging and error responses
- `app/middleware/logging.py` — `StructuredLoggingMiddleware`:
  - Emits one JSON log line per request: `request_id`, `method`, `path`, `status_code`, `duration_ms`
- `app/middleware/error_handler.py` — global error handlers:
  - Consistent `{"error": {"status_code": …, "detail": …, "request_id": …}}` envelope
  - Handles: `HTTPException`, `RequestValidationError`, unhandled `Exception` (500)
- `app/services/idempotency.py` — `get_cached_response()` / `store_idempotency_response()` service helpers
- `GET /api/v1/organizations` — list all orgs the authenticated user is a member of
- `PATCH /api/v1/organizations/{org_id}` — update org name / description (OWNER only), emits `org.updated` audit event
- `app/schemas/organization.py` — `OrgUpdateRequest` schema
- `tests/test_hardening.py` — 29 tests covering all M8/M9 features

### Changed
- `app/main.py` — wires all new middleware and error handlers; imports `limiter` from `app.core.limiter`
- `app/api/v1/organizations.py` — imports `OrgOwner`, `OrgUpdateRequest`; moved inline `select` import to top-level

---

## [0.7.0] — 2026-03-05 — M7: Audit Logging

### Added
- `app/services/audit.py` — `write_audit()` helper (flush-only, atomic with caller's commit)
- `app/schemas/audit_log.py` — `AuditLogOut` (renames ORM `metadata_` → API `metadata`)
- `app/api/v1/audit_logs.py` — 1 endpoint:
  - `GET /api/v1/organizations/{org_id}/audit-logs` — list audit events (ADMIN+)
    - Filters: `action`, `resource_type`, `resource_id`, `actor_user_id`, `since`, `until`
    - Pagination: `limit` (default 50, max 100), `offset`; ordered newest-first
- 16 audit actions instrumented across M3–M6 endpoints:

  | Action | Endpoint |
  |---|---|
  | `org.created` | POST /organizations |
  | `invite.sent` | POST /organizations/{id}/invites |
  | `invite.accepted` | POST /organizations/invites/accept/{token} |
  | `member.role_changed` | PATCH /organizations/{id}/members/{uid}/role |
  | `member.removed` | DELETE /organizations/{id}/members/{uid} |
  | `project.created` | POST /organizations/{id}/projects |
  | `project.updated` | PATCH /organizations/{id}/projects/{pid} |
  | `project.deleted` | DELETE /organizations/{id}/projects/{pid} |
  | `task.created` | POST /organizations/{id}/projects/{pid}/tasks |
  | `task.updated` | PATCH /organizations/{id}/tasks/{tid} |
  | `task.deleted` | DELETE /organizations/{id}/tasks/{tid} |
  | `task.label_added` | POST /organizations/{id}/tasks/{tid}/labels |
  | `task.label_removed` | DELETE /organizations/{id}/tasks/{tid}/labels/{name} |
  | `comment.created` | POST /organizations/{id}/tasks/{tid}/comments |
  | `comment.updated` | PATCH /organizations/{id}/comments/{cid} |
  | `comment.deleted` | DELETE /organizations/{id}/comments/{cid} |

- `tests/test_audit_logs.py` — 21 tests covering access control, event emission, response shape, filters, pagination, and org isolation

### Implementation Notes
- `AuditLog.metadata_` column avoids clash with SQLAlchemy internals; exposed as `metadata` in API via `AuditLogOut.from_orm()`
- `write_audit()` always flushes but never commits — mutations remain atomic with the surrounding transaction

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
