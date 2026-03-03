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

# Install dependencies
pip install -r requirements.txt

# Copy and fill environment variables
cp .env.example .env

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📂 Project Structure

```
Tenantrix/
├── app/
│   ├── main.py                    # FastAPI app factory
│   ├── core/
│   │   ├── config.py              # Pydantic settings (.env)
│   │   ├── security.py            # JWT + bcrypt helpers
│   │   ├── deps.py                # FastAPI dependencies
│   │   ├── pagination.py          # Offset pagination helper
│   │   ├── errors.py              # Global error handlers
│   │   └── logging.py             # Structured JSON logging
│   ├── db/
│   │   ├── base.py                # DeclarativeBase + mixins
│   │   ├── session.py             # Engine + SessionLocal
│   │   └── models/
│   │       ├── user.py
│   │       ├── org.py
│   │       ├── membership.py
│   │       ├── invite.py
│   │       ├── project.py
│   │       ├── task.py
│   │       ├── comment.py
│   │       ├── label.py
│   │       ├── audit.py
│   │       ├── token.py
│   │       └── idempotency.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── orgs.py
│   │   ├── projects.py
│   │   ├── tasks.py
│   │   ├── comments.py
│   │   └── audit.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── orgs.py
│   │   ├── projects.py
│   │   ├── tasks.py
│   │   ├── comments.py
│   │   └── audit.py
│   ├── services/
│   │   ├── auth.py
│   │   ├── orgs.py
│   │   ├── projects.py
│   │   ├── tasks.py
│   │   └── audit.py
│   ├── middlewares/
│   │   ├── request_id.py
│   │   └── rate_limit.py
│   └── utils/
│       ├── time.py
│       └── uuid.py
├── migrations/                    # Alembic migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── tests/
│   ├── conftest.py
│   ├── factories/
│   ├── test_auth.py
│   ├── test_orgs.py
│   ├── test_projects.py
│   ├── test_tasks.py
│   ├── test_comments.py
│   └── test_audit.py
├── .env.example
├── .env                           # Never committed
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── alembic.ini
├── README.md
├── ARCHITECTURE.md
├── API.md
└── CHANGELOG.md
```

---

## 🔧 Environment Variables

```bash
# App
APP_NAME=Tenantrix
APP_ENV=development
DEBUG=true
SECRET_KEY=your-super-secret-key-change-in-production
API_V1_PREFIX=/api/v1

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/tenantrix

# JWT
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# Rate Limiting
RATE_LIMIT_AUTH=5/minute

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

See `.env.example` for the full list.

---

## 📡 API Reference

Base URL: `/api/v1`  
Full API documentation: [`API.md`](API.md)  
Interactive docs (when running): `http://localhost:8000/docs`

### Endpoint Summary

| Group | Method | Path | Description |
|---|---|---|---|
| **Auth** | POST | `/auth/register` | Register new user |
| | POST | `/auth/login` | Login, get tokens |
| | POST | `/auth/refresh` | Rotate refresh token |
| | POST | `/auth/logout` | Revoke refresh token |
| | GET | `/auth/me` | Get current user |
| **Orgs** | POST | `/orgs` | Create organization |
| | GET | `/orgs` | List my organizations |
| | GET | `/orgs/{org_id}` | Get org details |
| | POST | `/orgs/{org_id}/invites` | Invite member |
| | POST | `/orgs/{org_id}/invites/accept` | Accept invite |
| | GET | `/orgs/{org_id}/members` | List members |
| | PATCH | `/orgs/{org_id}/members/{user_id}` | Update member role |
| | DELETE | `/orgs/{org_id}/members/{user_id}` | Remove member |
| **Projects** | POST | `/orgs/{org_id}/projects` | Create project |
| | GET | `/orgs/{org_id}/projects` | List projects |
| | GET | `/orgs/{org_id}/projects/{project_id}` | Get project |
| | PATCH | `/orgs/{org_id}/projects/{project_id}` | Update project |
| | DELETE | `/orgs/{org_id}/projects/{project_id}` | Archive project |
| **Tasks** | POST | `/orgs/{org_id}/projects/{project_id}/tasks` | Create task |
| | GET | `/orgs/{org_id}/projects/{project_id}/tasks` | List tasks |
| | GET | `/orgs/{org_id}/tasks/{task_id}` | Get task |
| | PATCH | `/orgs/{org_id}/tasks/{task_id}` | Update task |
| | DELETE | `/orgs/{org_id}/tasks/{task_id}` | Soft delete task |
| | POST | `/orgs/{org_id}/tasks/{task_id}/labels` | Add labels |
| | DELETE | `/orgs/{org_id}/tasks/{task_id}/labels/{label_name}` | Remove label |
| **Comments** | POST | `/orgs/{org_id}/tasks/{task_id}/comments` | Add comment |
| | GET | `/orgs/{org_id}/tasks/{task_id}/comments` | List comments |
| | PATCH | `/orgs/{org_id}/comments/{comment_id}` | Edit comment |
| | DELETE | `/orgs/{org_id}/comments/{comment_id}` | Delete comment |
| **Audit** | GET | `/orgs/{org_id}/audit` | List audit logs |
| **System** | GET | `/health` | Health check |

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
| M0 — Skeleton | 🔜 | Project setup, DB, health endpoint |
| M1 — Auth | 🔜 | Register, login, JWT, refresh tokens |
| M2 — Orgs & Members | 🔜 | Orgs, invites, RBAC |
| M3 — Projects | 🔜 | Project CRUD + archive |
| M4 — Tasks | 🔜 | Task CRUD + filters + labels |
| M5 — Comments | 🔜 | Comments + soft delete |
| M6 — Audit Logs | 🔜 | Audit trail |
| M7 — Production Features | 🔜 | Idempotency, request ID, logging |
| M8 — Testing & Hardening | 🔜 | Full test suite, RBAC tests |
| M9 — Docker & CI | 🔜 | Dockerfile, compose, GitHub Actions |

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
