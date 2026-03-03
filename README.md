# 🏢 Tenantrix

> **Multi-tenant SaaS Project Management API** — Production-grade backend built with FastAPI, PostgreSQL, and SQLAlchemy 2.0.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135+-green.svg)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.48-orange.svg)](https://sqlalchemy.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Environment Variables](#-environment-variables)
- [API Reference](#-api-reference)
- [Authentication](#-authentication)
- [RBAC Roles & Permissions](#-rbac-roles--permissions)
- [Running Tests](#-running-tests)
- [Docker](#-docker)
- [CI/CD](#-cicd)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)

---

## 🌐 Overview

**Tenantrix** is a backend-only SaaS API where multiple organizations (tenants) can manage projects, tasks, and teams — all with role-based access control, audit logging, and production-grade API patterns.

### Tenant Model

- **Single database, shared schema** — tenant isolation enforced by `org_id` on every row
- Every API request is scoped and authorized within a specific organization
- No data leakage between tenants is possible by design

---

## ✨ Features

### 🔐 Identity & Access
- Email/password registration and login
- JWT access tokens (short-lived, 15 minutes)
- Opaque refresh tokens with rotation and revoke-on-reuse
- Rate limiting on all auth endpoints
- Password hashing with bcrypt

### �� Organizations
- Create and manage organizations with unique slugs
- Invite members by email with role assignment
- Accept invites via secure token
- Org-level RBAC: `OWNER`, `ADMIN`, `MEMBER`, `VIEWER`
- Protect last owner from removal/demotion

### 📁 Projects
- Create, update, archive projects within organizations
- Unique project key per org (like Jira's `PROJ-123`)
- Filter by status, search by name/key
- Pagination on all list endpoints

### ✅ Tasks
- Full CRUD with soft delete
- Status workflow: `TODO` → `IN_PROGRESS` → `DONE` / `BLOCKED`
- Priority levels: `LOW`, `MEDIUM`, `HIGH`, `URGENT`
- Assign tasks to org members
- Due dates, labels/tags
- Rich filtering: status, assignee, priority, due date range, label, text search
- Sorting on multiple fields

### 💬 Comments
- Add, edit, soft-delete comments on tasks
- Author or ADMIN can edit/delete
- Pagination supported

### 🏷️ Labels
- Create org-scoped labels with optional color
- Attach/detach labels to tasks
- Filter tasks by label name

### 📋 Audit Logs
- Immutable audit trail for all significant actions
- Tracks: actor, action, entity type, entity ID, metadata, timestamp
- Filter by action, entity type, actor, date range

### 🛡️ Production Features
- Idempotency keys for all POST create endpoints
- Request ID middleware (`X-Request-ID` header)
- Structured JSON logging
- Consistent error schema across all endpoints
- DB transactions for multi-step operations
- Database indexes on all performance-critical columns
- Health endpoint

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Framework** | FastAPI 0.135+ |
| **ORM** | SQLAlchemy 2.0 (sync) |
| **Migrations** | Alembic |
| **Database** | PostgreSQL 16 |
| **Validation** | Pydantic v2 |
| **Auth** | PyJWT + passlib[bcrypt] |
| **Rate Limiting** | slowapi |
| **Server** | Uvicorn |
| **Testing** | Pytest + HTTPX TestClient |
| **Linting** | Ruff + Black |
| **Containers** | Docker + Docker Compose |
| **CI** | GitHub Actions |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL 16
- Docker & Docker Compose (optional but recommended)

### Option 1 — Docker (Recommended)

```bash
git clone https://github.com/DevaVirathan/Tenantrix.git
cd Tenantrix
cp .env.example .env
docker compose up --build
```

API will be live at: `http://localhost:8000`  
Swagger docs at: `http://localhost:8000/docs`

### Option 2 — Local Setup

```bash
# Clone and enter
git clone https://github.com/DevaVirathan/Tenantrix.git
cd Tenantrix

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install production dependencies
pip install -r requirements.txt

# (Optional) Install dev/test dependencies too
pip install -r requirements-dev.txt

# Copy and fill environment variables
cp .env.example .env
# Edit .env and set your POSTGRES_* credentials and SECRET_KEY

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> ⚠️ Always use the venv's uvicorn (`source .venv/bin/activate` first, or use `.venv/bin/uvicorn` directly) — running bare `uvicorn` from your system Python will fail if packages are only installed in the venv.

---

## 📂 Project Structure

```
Tenantrix/
├── app/
│   ├── main.py                    # FastAPI app factory + rate limiter
│   ├── core/
│   │   ├── config.py              # Pydantic settings (.env)
│   │   └── security.py            # JWT + bcrypt helpers
│   ├── api/
│   │   ├── deps.py                # FastAPI dependencies + RBAC helpers
│   │   └── v1/
│   │       ├── router.py          # Aggregates all sub-routers
│   │       ├── health.py          # Health check endpoint
│   │       ├── auth.py            # Auth endpoints (register/login/refresh/logout/me)
│   │       ├── organizations.py   # Org + invite + member endpoints
│   │       └── projects.py        # Project CRUD endpoints
│   ├── db/
│   │   ├── base.py                # DeclarativeBase + UUIDMixin + TimestampMixin
│   │   └── session.py             # Engine + SessionLocal + get_db
│   ├── models/
│   │   ├── __init__.py            # Imports all models (Alembic discovery)
│   │   ├── user.py
│   │   ├── organization.py
│   │   ├── membership.py          # OrgRole + MembershipStatus enums
│   │   ├── invite.py
│   │   ├── refresh_token.py
│   │   ├── project.py             # ProjectStatus enum
│   │   ├── task.py                # TaskStatus + TaskPriority enums, SoftDelete
│   │   ├── comment.py
│   │   ├── label.py
│   │   ├── task_label.py
│   │   ├── audit_log.py
│   │   └── idempotency_key.py
│   └── schemas/
│       ├── auth.py                # Register/Login/Token/Me schemas
│       ├── organization.py        # Org + Invite + Member schemas
│       └── project.py             # Project create/update/response schemas
├── alembic/                       # Alembic migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── tests/
│   ├── conftest.py                # DB fixtures + TestClient
│   ├── test_health.py
│   ├── test_models.py
│   ├── test_auth.py
│   ├── test_organizations.py
│   └── test_projects.py
├── .env.example
├── .env                           # Never committed
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── requirements.txt               # Production dependencies
├── requirements-dev.txt           # Dev + test dependencies
├── Makefile
├── alembic.ini
└── README.md
```

---

## 🔧 Environment Variables

```bash
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-db-password
POSTGRES_DB=tenantrix
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL=postgresql://postgres:your-db-password@localhost:5432/tenantrix

# Security — generate with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=change-me-to-a-random-64-char-hex-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application
ENVIRONMENT=development
VERSION=0.1.0
DEBUG=false

# Rate limiting (requests per minute per IP)
RATE_LIMIT_PER_MINUTE=60

# CORS — comma-separated allowed origins
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

See `.env.example` for the full list with comments.

---

## 📡 API Reference

Base URL: `/api/v1`  
Interactive docs (when running): `http://localhost:8000/docs`  
Alternative docs: `http://localhost:8000/redoc`

### Endpoint Summary

| Group | Method | Path | Description |
|---|---|---|---|
| **System** | GET | `/health` | Health check |
| **Auth** | POST | `/auth/register` | Register new user |
| | POST | `/auth/login` | Login, get tokens |
| | POST | `/auth/refresh` | Rotate refresh token |
| | POST | `/auth/logout` | Revoke refresh token |
| | GET | `/auth/me` | Get current user |
| **Organizations** | POST | `/organizations` | Create organization |
| | GET | `/organizations/{org_id}` | Get org details |
| | POST | `/organizations/{org_id}/invites` | Invite member by email |
| | POST | `/organizations/invites/accept/{token}` | Accept invite |
| | GET | `/organizations/{org_id}/members` | List members |
| | PATCH | `/organizations/{org_id}/members/{user_id}/role` | Update member role |
| | DELETE | `/organizations/{org_id}/members/{user_id}` | Remove member |
| **Projects** | POST | `/organizations/{org_id}/projects` | Create project |
| | GET | `/organizations/{org_id}/projects` | List projects |
| | GET | `/organizations/{org_id}/projects/{project_id}` | Get project |
| | PATCH | `/organizations/{org_id}/projects/{project_id}` | Update project |
| | DELETE | `/organizations/{org_id}/projects/{project_id}` | Delete project |

> All routes are prefixed with `/api/v1`. Interactive docs: `http://localhost:8000/docs`

---

## 🔐 Authentication

All endpoints (except `/auth/register`, `/auth/login`, `/health`) require:

```
Authorization: Bearer <access_token>
```

Access tokens expire in **15 minutes**. Use `POST /auth/refresh` with your refresh token to get a new pair.

### Idempotency

For all `POST` create endpoints, include:

```
Idempotency-Key: <unique-uuid-or-string>
```

Replaying the same request with the same key returns the cached response without side effects.

---

## 👥 RBAC Roles & Permissions

### Org-Level Roles

| Action | VIEWER | MEMBER | ADMIN | OWNER |
|---|:---:|:---:|:---:|:---:|
| Read org, projects, tasks, comments | ✅ | ✅ | ✅ | ✅ |
| Create/update tasks | ❌ | ✅ | ✅ | ✅ |
| Add/edit/delete own comments | ❌ | ✅ | ✅ | ✅ |
| Create/update projects | ❌ | ✅ | ✅ | ✅ |
| Archive projects | ❌ | ❌ | ✅ | ✅ |
| Invite members | ❌ | ❌ | ✅ | ✅ |
| Remove members | ❌ | ❌ | ✅ | ✅ |
| Edit/delete any comment | ❌ | ❌ | ✅ | ✅ |
| Change member roles | ❌ | ❌ | ❌ | ✅ |
| Delete org | ❌ | ❌ | ❌ | ✅ |
| Cannot remove last owner | — | — | — | 🔒 |

---

## 🧪 Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v

# Run with Docker
docker compose run test
```

Tests use a dedicated test database. Fixtures seed required data automatically.

---

## 🐳 Docker

```bash
# Start all services (api + postgres)
docker compose up --build

# Start in background
docker compose up -d

# Run migrations inside container
docker compose exec api alembic upgrade head

# Run tests inside container
docker compose run --rm test

# Stop all services
docker compose down

# Stop and remove volumes (wipes DB)
docker compose down -v
```

---

## ⚙️ CI/CD

GitHub Actions runs on every push and pull request to `main`:

1. **Lint** — `ruff check .` + `black --check .`
2. **Test** — `pytest` with PostgreSQL service container
3. **Build** — Docker image build verification

See `.github/workflows/ci.yml` for full configuration.

---

##  Roadmap

| Milestone | Status | Description |
|---|---|---|
| M0 — Skeleton | ✅ Done | Project setup, Docker, CI, health endpoint |
| M1 — Models & Migrations | ✅ Done | 12 ORM models, Alembic migration |
| M2 — Auth | ✅ Done | Register, login, JWT, refresh tokens with rotation |
| M3 — Org Management | ✅ Done | Orgs, invites, member RBAC (OWNER/ADMIN/MEMBER/VIEWER) |
| M4 — Projects | ✅ Done | Project CRUD + archive (5 endpoints, 28 tests) |
| M5 — Tasks | 🔜 Next | Task CRUD + status workflow + filters + labels |
| M6 — Comments | 🔜 | Comments + soft delete |
| M7 — Audit Logs | 🔜 | Immutable audit trail |
| M8 — Production Features | 🔜 | Idempotency keys, request ID middleware, structured logging |
| M9 — Docker & CI | 🔜 | Full Docker Compose, GitHub Actions hardening |

---

##  Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Commit your changes: `git commit -m 'feat: add my feature'`
4. Push: `git push origin feat/my-feature`
5. Open a Pull Request

Please follow the [Conventional Commits](https://www.conventionalcommits.org/) spec.

---

##  License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built with ❤️ using FastAPI + PostgreSQL*
