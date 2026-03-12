# CLAUDE.md — Tenantrix

## Project Overview

**Tenantrix** is a multi-tenant SaaS Project Management backend (à la Plane / Linear / Jira) built with FastAPI and SQLAlchemy 2.0. Multiple organizations (tenants) manage projects, tasks, sprints, comments, labels, and teams — all with role-based access control, audit logging, idempotency, and production-grade API patterns.

**Tenant model:** Single database, shared schema. Row-level isolation enforced by `org_id` on every table. No data leakage between tenants by design.

**Repo:** https://github.com/DevaVirathan/Tenantrix  
**Docs:** `http://localhost:8000/docs` (Swagger), `http://localhost:8000/redoc`

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12 |
| Framework | FastAPI 0.135+ |
| ORM | SQLAlchemy 2.0 (sync, `Session`) |
| Migrations | Alembic |
| Database | PostgreSQL 16 |
| Validation | Pydantic v2 |
| Auth | PyJWT + passlib[bcrypt] |
| Rate Limiting | slowapi |
| Server | Uvicorn |
| Testing | Pytest + HTTPX TestClient |
| Linting | Ruff + Black |
| Containers | Docker + Docker Compose |
| CI | GitHub Actions |

> **No Redis, no async ORM, no background worker yet.** SQLAlchemy 2.0 sync sessions with `get_db` dependency. Keep it sync unless explicitly upgrading.

---

## Architecture

```
Client
  → FastAPI App (app/main.py)
    → Middleware (RequestID, CORS, RateLimiter)
    → Router (app/api/v1/router.py)
      → Endpoint (thin — validate, call service/repo, return schema)
      → Dependency (app/api/deps.py — auth, RBAC, get_db, idempotency)
      → Model (app/models/ — SQLAlchemy ORM)
      → Schema (app/schemas/ — Pydantic v2 request/response)
    → DB Session (app/db/session.py — SessionLocal, get_db)
```

**Pattern per endpoint:**
1. Resolve `current_user` via `get_current_user` dep (JWT decode)
2. Resolve `org_membership` via `get_org_member` dep (checks `org_id` + role)
3. Call DB query inline or extract to a helper function — no separate service layer yet
4. Return Pydantic response schema

**RBAC:** Role hierarchy `OWNER > ADMIN > MEMBER > VIEWER`. Enforced in `app/api/deps.py` via `require_role(min_role)` guards called inside each endpoint.

---

## Project Structure

```
Tenantrix/
├── main.py                        # Entrypoint (imports app from app/main.py)
├── app/
│   ├── main.py                    # FastAPI factory — registers routers, middleware, rate limiter
│   ├── core/
│   │   ├── config.py              # Pydantic BaseSettings — reads .env
│   │   └── security.py            # JWT encode/decode, bcrypt hash/verify
│   ├── api/
│   │   ├── deps.py                # get_db, get_current_user, get_org_member, require_role
│   │   └── v1/
│   │       ├── router.py          # Aggregates all sub-routers under /api/v1
│   │       ├── health.py          # GET /health
│   │       ├── auth.py            # POST /auth/register, /login, /refresh, /logout — GET /me
│   │       ├── organizations.py   # Org CRUD, invites, member management
│   │       └── projects.py        # Project CRUD + archive
│   ├── db/
│   │   ├── base.py                # DeclarativeBase + UUIDMixin (uuid PK) + TimestampMixin (created_at, updated_at)
│   │   └── session.py             # Engine + SessionLocal + get_db generator
│   ├── models/
│   │   ├── __init__.py            # Imports all models (required for Alembic autogenerate)
│   │   ├── user.py                # User — email, hashed_password, is_active
│   │   ├── organization.py        # Organization — name, slug (unique), owner_id
│   │   ├── membership.py          # OrgMembership — org_id, user_id, role (OrgRole enum), status (MembershipStatus enum)
│   │   ├── invite.py              # OrgInvite — org_id, email, role, token (unique), expires_at, accepted_at
│   │   ├── refresh_token.py       # RefreshToken — user_id, token_hash, revoked, expires_at
│   │   ├── project.py             # Project — org_id, name, key (unique per org), description, status (ProjectStatus enum)
│   │   ├── task.py                # Task — org_id, project_id, title, description, status (TaskStatus), priority (TaskPriority), assignee_id, due_date, deleted_at
│   │   ├── comment.py             # Comment — org_id, task_id, author_id, body, deleted_at
│   │   ├── label.py               # Label — org_id, name, color
│   │   ├── task_label.py          # TaskLabel — task_id, label_id (association table)
│   │   ├── audit_log.py           # AuditLog — org_id, actor_id, action, entity_type, entity_id, metadata (JSON)
│   │   └── idempotency_key.py     # IdempotencyKey — key (unique), response_status, response_body, expires_at
│   └── schemas/
│       ├── auth.py                # RegisterRequest, LoginRequest, TokenResponse, MeResponse
│       ├── organization.py        # OrgCreate, OrgResponse, InviteCreate, MemberResponse, RoleUpdateRequest
│       └── project.py             # ProjectCreate, ProjectUpdate, ProjectResponse
├── alembic/
│   ├── env.py                     # Alembic env — imports all models, uses DATABASE_URL
│   ├── script.py.mako
│   └── versions/                  # Migration files
├── tests/
│   ├── conftest.py                # TestClient, test DB session, factory fixtures (org, user, membership, project)
│   ├── test_health.py
│   ├── test_models.py
│   ├── test_auth.py               # 15+ tests — register, login, refresh, logout, /me
│   ├── test_organizations.py      # 20+ tests — CRUD, invites, RBAC enforcement
│   └── test_projects.py           # 28 tests — CRUD, archive, RBAC, pagination
├── .env.example
├── docker-compose.yml             # api + postgres services
├── Dockerfile
├── pyproject.toml                 # Ruff + Black config
├── requirements.txt
├── requirements-dev.txt
├── Makefile
└── alembic.ini
```

---

## Key Commands

```bash
# Dev server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Docker (recommended)
docker compose up --build
docker compose exec api alembic upgrade head

# Migrations
alembic upgrade head                                    # Apply all pending
alembic revision --autogenerate -m "add sprints table"  # Generate from model changes
alembic downgrade -1                                    # Rollback one

# Linting & Formatting
ruff check .          # Lint
ruff check . --fix    # Auto-fix
black .               # Format

# Tests
pytest                                  # All tests
pytest --cov=app --cov-report=html      # With coverage
pytest tests/test_tasks.py -v           # Specific file
pytest -k "test_create_task" -v         # By name pattern
pytest -m "not slow"                    # Skip slow tests

# Makefile shortcuts
make lint
make test
make migrate
```

---

## Environment Variables

```bash
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-db-password
POSTGRES_DB=tenantrix
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL=postgresql://postgres:your-db-password@localhost:5432/tenantrix

# Security — generate: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=change-me-to-a-random-64-char-hex-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# App
ENVIRONMENT=development
VERSION=0.1.0
DEBUG=false

# Rate Limiting (requests per minute per IP)
RATE_LIMIT_PER_MINUTE=60

# CORS — comma-separated allowed origins
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## Conventions

### Naming
- Models: `<Entity>` class, `<entities>` table name → `Task` → `tasks`
- Schemas: `<Entity>Create`, `<Entity>Update`, `<Entity>Response`
- Enums: `<Entity><Field>` → `TaskStatus`, `TaskPriority`, `OrgRole`
- Routes: `app/api/v1/<domain>.py` — flat file per domain (sub-package only if >200 lines)
- Tests: `tests/test_<domain>.py`

### Model Conventions
- All PKs are UUIDs via `UUIDMixin` (from `app/db/base.py`)
- All models inherit `TimestampMixin` for `created_at` / `updated_at`
- Soft deletes: `deleted_at: datetime | None = None` — always filter with `.filter(Model.deleted_at.is_(None))`
- **Every model with user data MUST have `org_id: UUID` FK + db index**
- Add `Index('ix_<table>_<col>', '<col>')` for every column used in filters or ORDER BY

### Response Format
Simple and consistent. Success:
```json
{ "data": { ... } }
```
Use FastAPI's `HTTPException` with a `detail` string for errors. No custom wrapper needed yet.

### Idempotency
All `POST` create endpoints accept `Idempotency-Key: <uuid>` header. Handled by a shared dependency in `app/api/deps.py`. Reuse the existing dependency — do not create a new one.

### Auth & RBAC
- `get_current_user` → decodes JWT → returns `User` ORM object
- `get_org_member(org_id)` → queries `OrgMembership` → returns `(user, membership)` tuple
- `require_role(OrgRole.ADMIN)` → raises `403` if role is below threshold
- **Always apply `get_org_member` to any org-scoped endpoint.** Never query org data without scoping by `org_id` first.

### Testing Patterns
- `TestClient` + in-memory test DB (see `conftest.py` for setup)
- Fixtures: `org_fixture`, `user_fixture`, `member_fixture(role=OrgRole.MEMBER)`, `project_fixture`
- Pattern: seed fixture → call endpoint → assert status code + response body + DB state
- RBAC tests: test each endpoint with VIEWER/MEMBER/ADMIN/OWNER to confirm enforcement
- Target **28+ tests per domain** (matching M4 Projects benchmark)

### Git
- Conventional commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`
- PRs target `main`
- CI: `ruff check` + `black --check` + `pytest` on every push

---

## Completed Milestones

| Milestone | Status | What Was Built |
|-----------|--------|---------------|
| M0 — Skeleton | ✅ Done | FastAPI factory, Docker, CI pipeline, health endpoint |
| M1 — Models & Migrations | ✅ Done | 12 ORM models, Alembic env, initial migration |
| M2 — Auth | ✅ Done | Register, login, JWT (15min), refresh token rotation + revoke-on-reuse, bcrypt, rate limits |
| M3 — Org Management | ✅ Done | Org CRUD, email invite flow, accept-invite, member list, role update, remove member, last-owner guard |
| M4 — Projects | ✅ Done | Project CRUD + archive, unique key per org (`PROJ-123` style), status filter, search, pagination, 28 tests |

---

## Pending Milestones

### M5 — Tasks *(Current Focus — Start Here)*

The `Task` and `TaskLabel` models + migrations already exist. **No router, schemas, or tests exist yet.**

**Start here:** `app/schemas/task.py` → `app/api/v1/tasks.py` → register in `app/api/v1/router.py` → `tests/test_tasks.py`

**Endpoints to build:**

| Method | Path | Min Role | Description |
|--------|------|----------|-------------|
| POST | `/orgs/{org_id}/projects/{project_id}/tasks` | MEMBER | Create task |
| GET | `/orgs/{org_id}/projects/{project_id}/tasks` | VIEWER | List with filters, sort, pagination |
| GET | `/orgs/{org_id}/projects/{project_id}/tasks/{task_id}` | VIEWER | Task detail (with assignee + labels) |
| PATCH | `/orgs/{org_id}/projects/{project_id}/tasks/{task_id}` | MEMBER | Update fields |
| DELETE | `/orgs/{org_id}/projects/{project_id}/tasks/{task_id}` | MEMBER | Soft delete |
| PATCH | `/orgs/{org_id}/projects/{project_id}/tasks/{task_id}/status` | MEMBER | Status transition (validated) |
| POST | `/orgs/{org_id}/projects/{project_id}/tasks/{task_id}/assign` | MEMBER | Assign to org member |
| POST | `/orgs/{org_id}/projects/{project_id}/tasks/{task_id}/labels` | MEMBER | Attach label |
| DELETE | `/orgs/{org_id}/projects/{project_id}/tasks/{task_id}/labels/{label_id}` | MEMBER | Detach label |

**Status workflow** (enforce in PATCH /status — raise `422` on invalid transition):
```
TODO ──→ IN_PROGRESS ──→ DONE (terminal)
TODO ──→ BLOCKED
IN_PROGRESS ──→ BLOCKED
BLOCKED ──→ IN_PROGRESS
```

**Filter query params** for `GET /tasks`:
- `status` (multi-value: `?status=TODO&status=IN_PROGRESS`)
- `priority` (multi-value: `LOW | MEDIUM | HIGH | URGENT`)
- `assignee_id` (UUID)
- `label` (label name string)
- `due_before` / `due_after` (ISO date)
- `q` (text search on `title`)
- `sort_by` (`created_at | due_date | priority | status`, default `created_at`)
- `sort_dir` (`asc | desc`, default `desc`)
- `page` + `page_size` (default 20, max 100)

**Key rules:**
- Always filter by both `org_id` AND `project_id` — never by `task_id` alone
- Soft delete: set `deleted_at = datetime.utcnow()`, all list/get queries must add `.filter(Task.deleted_at.is_(None))`
- Assignee must be an active member of the org — validate before setting `assignee_id`
- Label attach: verify `label.org_id == org_id` before creating `TaskLabel` row
- Use `joinedload(Task.assignee)` + `joinedload(Task.labels)` on detail and list endpoints to avoid N+1 queries

---

### M6 — Comments

**Endpoints** (`app/api/v1/comments.py`):

| Method | Path | Min Role | Notes |
|--------|------|----------|-------|
| POST | `/orgs/{org_id}/tasks/{task_id}/comments` | MEMBER | Create comment |
| GET | `/orgs/{org_id}/tasks/{task_id}/comments` | VIEWER | List (paginated, newest first) |
| PATCH | `/orgs/{org_id}/tasks/{task_id}/comments/{comment_id}` | MEMBER | Edit — own only (ADMIN can edit any) |
| DELETE | `/orgs/{org_id}/tasks/{task_id}/comments/{comment_id}` | MEMBER | Soft delete — own or ADMIN+ |

**Rules:** Author (`comment.author_id == current_user.id`) OR `ADMIN`/`OWNER` can mutate. Soft delete via `deleted_at`. Cursor-based pagination by `created_at DESC`.

---

### M7 — Labels Management

**Endpoints** (`app/api/v1/labels.py`):

| Method | Path | Min Role | Notes |
|--------|------|----------|-------|
| POST | `/orgs/{org_id}/labels` | ADMIN | Create org-scoped label with optional hex color |
| GET | `/orgs/{org_id}/labels` | VIEWER | List all labels |
| PATCH | `/orgs/{org_id}/labels/{label_id}` | ADMIN | Update name/color |
| DELETE | `/orgs/{org_id}/labels/{label_id}` | ADMIN | Delete + cascade-detach from all tasks |

**Notes:** `Label` model already exists. On delete: cascade-delete all `TaskLabel` rows for that `label_id` in same transaction.

---

### M8 — Audit Logs

**Goal:** Immutable, queryable audit trail. `AuditLog` model already exists.

**Write helper** — create `app/utils/audit.py`:
```python
def log_action(db, org_id, actor_id, action, entity_type, entity_id, metadata=None):
    entry = AuditLog(org_id=org_id, actor_id=actor_id, action=action,
                     entity_type=entity_type, entity_id=entity_id, metadata=metadata or {})
    db.add(entry)
    # Do NOT commit here — caller commits with their transaction
```

**Call `log_action` after every successful write** on: task create/update/delete/status-change/assign, comment create/delete, member invite/role-change/remove, project create/archive.

**Read endpoints** (`app/api/v1/audit.py`):

| Method | Path | Min Role |
|--------|------|----------|
| GET | `/orgs/{org_id}/audit-logs` | ADMIN |
| GET | `/orgs/{org_id}/audit-logs/{entity_type}/{entity_id}` | ADMIN |

Filters: `actor_id`, `action`, `entity_type`, `from_date`, `to_date`. Paginated by `created_at DESC`.

---

### M9 — Sprints

**Goal:** Time-boxed sprints (Cycles) per project.

**New models to create:**
- `Sprint` — `org_id`, `project_id`, `name`, `goal`, `start_date`, `end_date`, `status` (`PLANNED | ACTIVE | COMPLETED`)
- `SprintTask` — `sprint_id`, `task_id` (association table)

**Endpoints** (`app/api/v1/sprints.py`):

| Method | Path | Notes |
|--------|------|-------|
| POST | `/orgs/{org_id}/projects/{project_id}/sprints` | Create sprint (status=PLANNED) |
| GET | `/orgs/{org_id}/projects/{project_id}/sprints` | List (filter by status) |
| PATCH | `/orgs/{org_id}/projects/{project_id}/sprints/{sprint_id}` | Update / start / complete |
| DELETE | `/orgs/{org_id}/projects/{project_id}/sprints/{sprint_id}` | Delete (PLANNED only) |
| POST | `…/sprints/{sprint_id}/tasks` | Add task to sprint |
| DELETE | `…/sprints/{sprint_id}/tasks/{task_id}` | Remove task from sprint |
| GET | `…/sprints/{sprint_id}/tasks` | List tasks in sprint (with same filters as M5) |

**Business rules:**
- Only one `ACTIVE` sprint per project — enforce on status transition to `ACTIVE`
- Completing a sprint: set `status=COMPLETED`, delete all `SprintTask` rows for incomplete tasks (move them back to backlog)

---

### M10 — Production Hardening

- [ ] Verify `X-Request-ID` middleware propagates to response headers
- [ ] Replace any `print` statements with `structlog` or `python-json-logger`
- [ ] Add Prometheus metrics via `prometheus-fastapi-instrumentator` at `/metrics`
- [ ] Add Sentry SDK for error tracking
- [ ] Standardize pagination — pick offset or cursor, apply consistently across all list endpoints
- [ ] Add OpenAPI router tags + descriptions for clean Swagger UI grouping
- [ ] Tune DB connection pooling in `app/db/session.py` (`pool_size=10`, `max_overflow=20`)
- [ ] Add `HEALTHCHECK` to Dockerfile

---

## RBAC Quick Reference

| Action | VIEWER | MEMBER | ADMIN | OWNER |
|--------|--------|--------|-------|-------|
| Read anything | ✅ | ✅ | ✅ | ✅ |
| Create/update/delete tasks | ❌ | ✅ | ✅ | ✅ |
| Comment on tasks | ❌ | ✅ | ✅ | ✅ |
| Create/update projects | ❌ | ✅ | ✅ | ✅ |
| Archive projects | ❌ | ❌ | ✅ | ✅ |
| Manage labels | ❌ | ❌ | ✅ | ✅ |
| Invite / remove members | ❌ | ❌ | ✅ | ✅ |
| View audit logs | ❌ | ❌ | ✅ | ✅ |
| Edit/delete any comment | ❌ | ❌ | ✅ | ✅ |
| Change member roles | ❌ | ❌ | ❌ | ✅ |
| Delete org | ❌ | ❌ | ❌ | ✅ |
| Last-owner protection | — | — | — | 🔒 |

---

## Current Focus

- **Current Milestone:** M5 — Tasks
- **Repo state:** `Task` + `TaskLabel` models + migrations exist. No schemas, no router, no tests for tasks yet.
- **Agent entry point:** Open `app/schemas/project.py` for schema pattern reference → create `app/schemas/task.py` → create `app/api/v1/tasks.py` following `projects.py` patterns → register prefix `/orgs/{org_id}/projects/{project_id}/tasks` in `app/api/v1/router.py` → write `tests/test_tasks.py` (28+ tests covering CRUD, status workflow, RBAC, filters, soft delete).
- **Blocked On:** Nothing. All FK dependencies (org, membership, project, label) are already in place.
- **Next after M5:** M6 Comments → M7 Labels → M8 Audit Logs → M9 Sprints → M10 Production Hardening.