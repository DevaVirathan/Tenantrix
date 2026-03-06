# Tenantrix — Architecture Guide

> Deep-dive into the system design, data model, and technical decisions behind Tenantrix.

---

## Table of Contents

- [System Overview](#system-overview)
- [Multi-Tenancy Strategy](#multi-tenancy-strategy)
- [Data Model](#data-model)
- [Authentication Design](#authentication-design)
- [RBAC Design](#rbac-design)
- [Request Lifecycle](#request-lifecycle)
- [Layered Architecture](#layered-architecture)
- [Key Design Decisions](#key-design-decisions)
- [Database Indexes](#database-indexes)
- [Error Handling](#error-handling)
- [Pagination](#pagination)
- [Idempotency](#idempotency)
- [Audit Logging](#audit-logging)
- [Soft Deletes](#soft-deletes)
- [Security Checklist](#security-checklist)

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT (HTTP)                           │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FASTAPI APPLICATION                         │
│                                                                 │
│  ┌──────────────┐  ┌────────────┐  ┌───────────────────────┐   │
│  │  Middleware  │  │  Routers   │  │   OpenAPI / Swagger    │   │
│  │ • Request ID │  │ /auth      │  │   /docs  /redoc        │   │
│  │ • Rate Limit │  │ /orgs      │  └───────────────────────┘   │
│  │ • Logging    │  │ /projects  │                               │
│  │ • Error Hdlr │  │ /tasks     │                               │
│  └──────────────┘  │ /comments  │                               │
│                    │ /audit     │                               │
│                    └─────┬──────┘                               │
│                          │                                      │
│               ┌──────────▼──────────┐                          │
│               │      Services       │                          │
│               │  Business Logic     │                          │
│               │  Transactions       │                          │
│               │  Audit Writes       │                          │
│               └──────────┬──────────┘                          │
│                          │                                      │
│               ┌──────────▼──────────┐                          │
│               │   SQLAlchemy ORM    │                          │
│               │   Models / Queries  │                          │
│               └──────────┬──────────┘                          │
└──────────────────────────┼──────────────────────────────────────┘
                           │
                           ▼
          ┌────────────────────────────────┐
          │        PostgreSQL 16           │
          │  tenantrix database            │
          └────────────────────────────────┘
```

---

## Multi-Tenancy Strategy

Tenantrix uses the **Shared Database, Shared Schema** multi-tenancy pattern.

### How It Works

Every business entity table contains an `org_id` (UUID) foreign key column. All queries are filtered by `org_id` at the service layer.

```
organizations
     │
     ├── memberships   (org_id, user_id, role)
     ├── invites       (org_id, email, token_hash)
     ├── projects      (org_id, name, key)
     │     └── tasks   (org_id, project_id, ...)
     │           ├── comments    (org_id, task_id, ...)
     │           └── task_labels (task_id, label_id)
     ├── labels        (org_id, name)
     └── audit_logs    (org_id, actor_id, action, ...)
```

### Why This Approach

| Factor | Decision |
|---|---|
| Simplicity | Single DB, single schema — no dynamic schema switching |
| Cost | No per-tenant DB overhead |
| Isolation | `org_id` enforced on every query via service layer |
| Scalability | Can shard by `org_id` later if needed |
| Risk | SQL injection bypassing `org_id` filters — mitigated via ORM and strict dependency injection |

---

## Data Model

### Entity Relationship Diagram (Simplified)

```
users
  id (PK, UUID)
  email (UNIQUE)
  password_hash
  is_active
  created_at / updated_at

organizations
  id (PK, UUID)
  name
  slug (UNIQUE)
  created_by → users.id
  created_at / updated_at

memberships
  id (PK, UUID)
  org_id → organizations.id
  user_id → users.id
  role: OWNER | ADMIN | MEMBER | VIEWER
  status: ACTIVE | INVITED
  UNIQUE(org_id, user_id)

invites
  id (PK, UUID)
  org_id → organizations.id
  email
  role
  token_hash (UNIQUE)
  expires_at
  accepted_at (nullable)
  UNIQUE(org_id, email)

projects
  id (PK, UUID)
  org_id → organizations.id
  name
  key (e.g. "BR")
  description
  status: ACTIVE | ARCHIVED
  created_at / updated_at
  UNIQUE(org_id, key)

tasks
  id (PK, UUID)
  org_id → organizations.id
  project_id → projects.id
  title
  description
  status: TODO | IN_PROGRESS | DONE | BLOCKED
  priority: LOW | MEDIUM | HIGH | URGENT
  assignee_user_id → users.id (nullable)
  due_date (nullable)
  deleted_at (nullable)           ← soft delete
  created_at / updated_at

comments
  id (PK, UUID)
  org_id → organizations.id
  task_id → tasks.id
  author_user_id → users.id
  body
  deleted_at (nullable)           ← soft delete
  created_at / updated_at

labels
  id (PK, UUID)
  org_id → organizations.id
  name
  color (nullable)
  UNIQUE(org_id, name)

task_labels  (many-to-many)
  task_id → tasks.id
  label_id → labels.id
  PRIMARY KEY (task_id, label_id)

audit_logs
  id (PK, UUID)
  org_id → organizations.id
  actor_user_id → users.id (nullable)
  action (string, e.g. "task.created")
  entity_type (string, e.g. "task")
  entity_id (UUID)
  metadata (JSONB)
  created_at

refresh_tokens
  id (PK, UUID)
  user_id → users.id
  token_hash (UNIQUE)
  expires_at
  revoked_at (nullable)
  created_at

idempotency_keys
  id (PK, UUID)
  org_id → organizations.id
  user_id → users.id
  key (client-provided string)
  request_hash (method + path + body hash)
  response_code
  response_body (JSONB)
  created_at
  UNIQUE(org_id, user_id, key)
```

---

## Authentication Design

### Token Flow

```
1. POST /auth/login
   ├── Verify email + bcrypt password hash
   ├── Generate JWT access token  (exp: 15 min, HS256, contains user_id)
   ├── Generate random refresh token (32 bytes, stored as SHA-256 hash in DB)
   └── Return { access_token, refresh_token, token_type, expires_in }

2. API Request
   ├── Client sends: Authorization: Bearer <access_token>
   ├── FastAPI dependency decodes JWT
   ├── Checks expiry, signature
   └── Injects current_user into route

3. POST /auth/refresh
   ├── Client sends: { refresh_token: "..." }
   ├── Hash the token, look up in refresh_tokens table
   ├── Check: not expired, not revoked
   ├── REVOKE old token immediately (revoked_at = now)
   ├── Generate new access + refresh token pair
   ├── If old token was already revoked → REVOKE ALL sessions for user (reuse attack)
   └── Return new token pair

4. POST /auth/logout
   ├── Hash the refresh token, look up in DB
   ├── Set revoked_at = now
   └── 204 No Content
```

### Why Opaque Refresh Tokens (not JWT refresh)

- **Revocable**: Stored in DB, single revocation query
- **Rotation + Reuse Detection**: If a revoked token is replayed, all sessions are killed
- **Simpler**: No need to maintain a blocklist for JWTs
- **Secure**: Only SHA-256 hash stored, not the raw token

---

## RBAC Design

### Role Hierarchy

```
OWNER  >  ADMIN  >  MEMBER  >  VIEWER
```

### Enforcement Pattern

Every protected endpoint uses a FastAPI dependency:

```python
# Level 1: Authentication
current_user = Depends(get_current_user)       # decodes JWT

# Level 2: Org Membership
membership = Depends(get_membership(org_id))   # checks org_id + user_id

# Level 3: Role Check
_ = Depends(require_role(OrgRole.MEMBER))      # checks role >= required
```

### Role Comparison

Roles are stored as enums and compared by numeric weight:

```
VIEWER  = 1
MEMBER  = 2
ADMIN   = 3
OWNER   = 4
```

`require_role(MEMBER)` passes for MEMBER, ADMIN, and OWNER.

### Special Guards

- **Last owner protection**: Cannot remove or demote the last OWNER of an org
- **Self-demotion**: OWNER cannot change their own role (must transfer ownership first)
- **Comment ownership**: MEMBER can only edit/delete their own comments; ADMIN+ can edit/delete any

---

## Request Lifecycle

```
HTTP Request
     │
     ▼
[RequestIDMiddleware]
  • Generate/attach X-Request-ID header
  • Bind request_id to logging context
     │
     ▼
[RateLimitMiddleware]  (auth routes only)
  • Check Redis/memory counter
  • 429 Too Many Requests if exceeded
     │
     ▼
[FastAPI Router]
  • Path matching
  • Dependency injection starts
     │
     ▼
[Dependencies: Depends()]
  1. get_db()          → yields SQLAlchemy Session
  2. get_current_user() → decodes JWT → loads User
  3. get_membership()   → loads Membership for org_id
  4. require_role()     → checks role weight
  5. idempotency_dep()  → check/store idempotency key (if POST)
     │
     ▼
[Router Handler]
  • Validates request body via Pydantic schema
  • Calls service function
     │
     ▼
[Service Layer]
  • Business logic
  • DB queries via SQLAlchemy
  • Wrapped in DB transaction if multi-step
  • Calls audit_service.log() for tracked actions
     │
     ▼
[Response]
  • Pydantic response schema serializes ORM model
  • HTTP status code set
  • X-Request-ID echoed in response headers
```

---

## Layered Architecture

```
┌────────────────────────────────────────────┐
│                 ROUTERS                    │
│   HTTP in → validate → call service → out │
│   Thin layer, no business logic            │
└──────────────────┬─────────────────────────┘
                   │ calls
┌──────────────────▼─────────────────────────┐
│                SERVICES                    │
│   All business logic lives here            │
│   Handles DB transactions                  │
│   Calls audit logging                      │
│   Raises HTTPException on violations       │
└──────────────────┬─────────────────────────┘
                   │ uses
┌──────────────────▼─────────────────────────┐
│              ORM MODELS                    │
│   SQLAlchemy 2.0 Mapped Classes            │
│   No logic — pure data representation     │
└──────────────────┬─────────────────────────┘
                   │ queries
┌──────────────────▼─────────────────────────┐
│              POSTGRESQL                    │
└────────────────────────────────────────────┘
```

### Why This Layering

- **Routers** stay thin — easy to read, easy to test
- **Services** are testable in isolation (mock the session)
- **Models** are pure data — no circular imports
- **Schemas** are separate from models — prevents tight coupling

---

## Database Indexes

Performance-critical indexes defined in migrations:

```sql
-- Tenant isolation (most important)
CREATE INDEX idx_projects_org_id ON projects(org_id);
CREATE INDEX idx_tasks_org_id ON tasks(org_id);
CREATE INDEX idx_tasks_org_project ON tasks(org_id, project_id);
CREATE INDEX idx_comments_org_id ON comments(org_id);
CREATE INDEX idx_audit_logs_org_id ON audit_logs(org_id);

-- Frequent filter columns
CREATE INDEX idx_tasks_status ON tasks(org_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_tasks_assignee ON tasks(org_id, assignee_user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_tasks_due_date ON tasks(org_id, due_date) WHERE deleted_at IS NULL;
CREATE INDEX idx_projects_status ON projects(org_id, status);

-- Auth lookups
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens(token_hash);
CREATE INDEX idx_invites_token_hash ON invites(token_hash);

-- Audit log queries
CREATE INDEX idx_audit_logs_actor ON audit_logs(org_id, actor_user_id);
CREATE INDEX idx_audit_logs_entity ON audit_logs(org_id, entity_type, entity_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(org_id, created_at DESC);

-- Memberships
CREATE INDEX idx_memberships_user_id ON memberships(user_id);
```

---

## Error Handling

### Consistent Error Schema

All errors return the same shape:

```json
{
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "Task with id abc123 does not exist in this organization.",
    "details": {}
  }
}
```

### HTTP Status Code Conventions

| Code | Usage |
|---|---|
| `200` | Successful GET / PATCH |
| `201` | Successful POST (resource created) |
| `204` | Successful DELETE (no body) |
| `400` | Bad request / validation error |
| `401` | Not authenticated (missing/invalid token) |
| `403` | Authenticated but not authorized (wrong role) |
| `404` | Resource not found (or not visible to tenant) |
| `409` | Conflict (duplicate slug, duplicate invite, etc.) |
| `422` | Pydantic validation failure |
| `429` | Rate limit exceeded |
| `500` | Unexpected server error |

### Global Exception Handler

A global handler in `app/core/errors.py` catches:
- `HTTPException` → formatted error response
- `RequestValidationError` → 422 with field-level details
- Unhandled exceptions → 500 with request_id for tracing

---

## Pagination

All list endpoints support offset pagination.

### Query Parameters

| Param | Default | Max | Description |
|---|---|---|---|
| `limit` | `20` | `100` | Items per page |
| `offset` | `0` | — | Number of items to skip |

### Response Shape

```json
{
  "items": [...],
  "limit": 20,
  "offset": 0,
  "total": 143
}
```

### Implementation

A reusable `PaginationParams` dependency in `app/core/pagination.py`:

```python
class PaginationParams:
    def __init__(self, limit: int = 20, offset: int = 0):
        self.limit = min(limit, 100)
        self.offset = offset
```

---

## Idempotency

### How It Works

1. Client sends `Idempotency-Key: <unique-string>` header with any `POST` create request
2. Server checks `idempotency_keys` table for `(org_id, user_id, key)`
3. **If found** → return cached `response_code` + `response_body` immediately
4. **If not found** → execute the request, store result, return response

### Storage

```
idempotency_keys
  org_id, user_id, key       → UNIQUE index
  request_hash               → SHA-256 of method + path + body
  response_code              → e.g. 201
  response_body              → JSONB
  created_at                 → keys expire after 24 hours (cleanup job)
```

### Why Per (org_id, user_id, key) and Not Just Key

- Keys are user-scoped: two users can use the same key string without collision
- Keys are org-scoped: prevents cross-tenant idempotency collisions

---

## Audit Logging

### Tracked Actions

| Action | Trigger |
|---|---|
| `auth.register` | User registered |
| `auth.login` | User logged in |
| `org.created` | Organization created |
| `org.member_invited` | Member invited |
| `org.invite_accepted` | Invite accepted |
| `org.member_role_changed` | Member role updated |
| `org.member_removed` | Member removed |
| `project.created` | Project created |
| `project.updated` | Project updated |
| `project.archived` | Project archived |
| `task.created` | Task created |
| `task.updated` | Task updated |
| `task.deleted` | Task soft-deleted |
| `task.assigned` | Task assigned to user |
| `task.status_changed` | Task status changed |
| `task.label_added` | Label added to task |
| `task.label_removed` | Label removed from task |
| `comment.created` | Comment added |
| `comment.updated` | Comment edited |
| `comment.deleted` | Comment soft-deleted |

### Audit Log Entry Shape

```json
{
  "id": "uuid",
  "org_id": "uuid",
  "actor_user_id": "uuid",
  "action": "task.status_changed",
  "entity_type": "task",
  "entity_id": "uuid",
  "metadata": {
    "from_status": "TODO",
    "to_status": "IN_PROGRESS",
    "title": "Add RBAC middleware"
  },
  "created_at": "2026-03-03T10:00:00Z"
}
```

### Design Notes

- Audit logs are **append-only** — no updates or deletes
- Written inside the same DB transaction as the action
- `actor_user_id` can be null for system-generated events

---

## Soft Deletes

Tasks and Comments support soft deletes via `deleted_at` timestamp.

### Behavior

- `DELETE /tasks/{id}` → sets `deleted_at = now()`, returns `204`
- All list queries include `WHERE deleted_at IS NULL` automatically
- `GET /tasks/{id}` returns `404` if `deleted_at` is set
- Audit log entry is written on soft delete

### Why Not Hard Delete

- Maintains referential integrity (comments reference tasks)
- Allows potential undelete functionality in future
- Audit trail remains intact

### Implementation

A `SoftDeleteMixin` on the base model adds:

```python
deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)

@property
def is_deleted(self) -> bool:
    return self.deleted_at is not None
```

Service queries always apply `.where(Model.deleted_at.is_(None))`.

---

## Security Checklist

| Item | Status | Notes |
|---|---|---|
| Password hashing | bcrypt via passlib | Cost factor 12 |
| JWT algorithm | HS256 | Secret key from env |
| JWT expiry | 15 minutes | Short-lived |
| Refresh token storage | SHA-256 hash only | Raw token never stored |
| Refresh token rotation | On every use | New pair issued |
| Reuse attack detection | Revoke all sessions | On stale token replay |
| Rate limiting | Auth endpoints | 5 req/min per IP |
| Input validation | Pydantic v2 | All request bodies |
| Org isolation | org_id on every query | Service layer enforced |
| Last owner protection | Guard in service | Cannot demote/remove |
| SQL injection | SQLAlchemy ORM | Parameterized queries |
| Sensitive env vars | .env file | Never committed |
| Request tracing | X-Request-ID | All requests |
| HTTPS | Reverse proxy (nginx) | Not handled in app |
