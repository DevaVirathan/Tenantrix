# Tenantrix Web — Frontend Architecture Guide

> Deep-dive into the frontend system design, project structure, state management,
> auth strategy, and technical decisions for the Tenantrix React SPA.

---

## Table of Contents

- [System Overview](#system-overview)
- [Tech Stack](#tech-stack)
- [Repo Strategy](#repo-strategy)
- [Project Structure](#project-structure)
- [Auth Architecture](#auth-architecture)
- [State Management](#state-management)
- [API Client Layer](#api-client-layer)
- [RBAC on the Frontend](#rbac-on-the-frontend)
- [Routing Strategy](#routing-strategy)
- [Component Architecture](#component-architecture)
- [Form Validation Strategy](#form-validation-strategy)
- [Error Handling](#error-handling)
- [Module Plan](#module-plan)
- [Environment Variables](#environment-variables)
- [Key Design Decisions](#key-design-decisions)

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                      BROWSER (React SPA)                            │
│                                                                     │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────────────┐   │
│  │  React Router │  │ TanStack Query│  │     Zustand Store     │   │
│  │  (Pages/Views)│  │ (Server State)│  │  (activeOrg, user,    │   │
│  │               │  │  Cache+Sync   │  │   sidebarOpen, role)  │   │
│  └───────┬───────┘  └──────┬────────┘  └───────────────────────┘   │
│          │                 │                                        │
│          └────────┬────────┘                                        │
│                   │                                                 │
│          ┌────────▼────────┐                                        │
│          │   api-client.ts │  ← ky instance                        │
│          │   (fetch wrapper│    + auth interceptor                  │
│          │    + token mgmt)│    + 401 auto-refresh                  │
│          └────────┬────────┘                                        │
└───────────────────┼─────────────────────────────────────────────────┘
                    │  HTTP (CORS)
                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (localhost:8000)                  │
│               /api/v1/auth | /organizations | /projects             │
│                      /tasks | /comments | /audit-logs               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Choice | Version | Why |
|---|---|---|---|
| **Framework** | Vite + React | React 19, Vite 6 | Fast HMR, minimal config, SPA fits this app perfectly |
| **Language** | TypeScript | 5.x | Type safety end-to-end, mirrors Pydantic models |
| **Routing** | React Router v7 | 7.x | File-system routing, nested layouts, loader pattern |
| **Styling** | Tailwind CSS + shadcn/ui | Tailwind v4 | Utility-first, shadcn components are accessible + customisable |
| **UI Theme** | Jira-inspired | — | Dense, information-heavy, status-driven |
| **Dark Mode** | Yes (default dark) | — | Toggleable via ThemeProvider |
| **Server State** | TanStack Query | v5 | Caching, refetching, mutations, optimistic updates |
| **Client State** | Zustand | v5 | Lightweight store — active org, user session, UI state |
| **Forms** | React Hook Form + Zod | RHF 7, Zod 3 | Performant, validation mirrors backend Pydantic rules |
| **HTTP Client** | ky | latest | Lightweight fetch wrapper, interceptors for token refresh |
| **Auth Storage** | httpOnly cookies | — | Secure — no XSS risk, tokens never in JS memory |
| **Drag & Drop** | @dnd-kit/core | v6 | Kanban board task reordering across status columns |
| **Icons** | Lucide React | latest | Ships with shadcn/ui, tree-shakable |
| **Date** | date-fns | v4 | formatDistanceToNow, format, parseISO |
| **Toasts** | Sonner | latest | Ships with shadcn/ui, minimal API |

---

## Repo Strategy

**Recommendation: Monorepo** — `frontend/` folder inside the existing `Tenantrix` repo.

### Why Monorepo (not separate repo)

| Factor | Monorepo |
|---|---|
| Single `git clone` | Everything in one place |
| Shared docs | Frontend/backend docs colocated in `Docs/` |
| Coordinated deploys | Backend + frontend versioned together |
| Simpler CI/CD | One GitHub Actions workflow file |
| TypeScript types | Can share type definitions in a `shared/` package later |

### Structure

```
Tenantrix/                        ← existing backend repo root
├── app/                          ← FastAPI backend (existing)
├── alembic/                      ← DB migrations (existing)
├── tests/                        ← Backend tests (existing)
├── Docs/
│   ├── ARCHITECTURE.md           ← Backend architecture
│   ├── API.md                    ← Backend API reference
│   ├── CHANGELOG.md              ← Backend changelog
│   └── Frontend/                 ← NEW
│       ├── FRONTEND-ARCHITECTURE.md
│       ├── FRONTEND-API.md
│       └── FRONTEND-CHANGELOG.md
├── frontend/                     ← NEW — Vite React SPA
│   ├── src/
│   ├── public/
│   ├── index.html
│   ├── vite.config.ts
│   ├── package.json
│   └── tsconfig.json
├── .env                          ← Backend env
├── pyproject.toml
└── README.md
```

---

## Project Structure

```
frontend/
├── public/
│   ├── favicon.ico
│   └── logo.svg
│
├── src/
│   ├── main.tsx                     # App entry point
│   ├── app.tsx                      # Router + Providers wrapper
│   │
│   ├── pages/                       # Route-level page components
│   │   ├── auth/
│   │   │   ├── login.tsx
│   │   │   ├── register.tsx
│   │   │   └── accept-invite.tsx    # /invite/:token
│   │   ├── orgs/
│   │   │   ├── index.tsx            # /orgs — org list
│   │   │   └── [orgId]/
│   │   │       ├── dashboard.tsx    # /orgs/:orgId
│   │   │       ├── settings.tsx     # /orgs/:orgId/settings
│   │   │       ├── members.tsx      # /orgs/:orgId/members
│   │   │       ├── invites.tsx      # /orgs/:orgId/invites
│   │   │       ├── audit-logs.tsx   # /orgs/:orgId/audit-logs
│   │   │       └── projects/
│   │   │           ├── index.tsx    # /orgs/:orgId/projects
│   │   │           └── [projectId]/
│   │   │               ├── board.tsx      # /…/projects/:id/board
│   │   │               ├── list.tsx       # /…/projects/:id/list
│   │   │               └── settings.tsx   # /…/projects/:id/settings
│   │   └── not-found.tsx
│   │
│   ├── layouts/
│   │   ├── auth-layout.tsx          # Centered card — login/register
│   │   └── dashboard-layout.tsx     # Sidebar + TopBar + Outlet
│   │
│   ├── components/
│   │   ├── ui/                      # shadcn/ui primitives (auto-generated)
│   │   │
│   │   ├── layout/
│   │   │   ├── sidebar.tsx
│   │   │   ├── top-bar.tsx
│   │   │   ├── breadcrumb.tsx
│   │   │   ├── org-switcher.tsx     # Dropdown — all user orgs
│   │   │   ├── user-menu.tsx        # Avatar + logout
│   │   │   └── mobile-nav.tsx
│   │   │
│   │   ├── auth/
│   │   │   ├── login-form.tsx
│   │   │   ├── register-form.tsx
│   │   │   └── password-strength-indicator.tsx
│   │   │
│   │   ├── orgs/
│   │   │   ├── org-card.tsx
│   │   │   ├── create-org-dialog.tsx
│   │   │   ├── member-table.tsx
│   │   │   ├── invite-dialog.tsx
│   │   │   ├── invite-list.tsx
│   │   │   └── role-badge.tsx
│   │   │
│   │   ├── projects/
│   │   │   ├── project-card.tsx
│   │   │   ├── create-project-dialog.tsx
│   │   │   └── project-status-badge.tsx
│   │   │
│   │   ├── tasks/
│   │   │   ├── kanban-board.tsx         # @dnd-kit DndContext wrapper
│   │   │   ├── kanban-column.tsx        # SortableContext per status
│   │   │   ├── task-card.tsx            # Draggable card
│   │   │   ├── task-detail-panel.tsx    # Slide-over panel (Sheet)
│   │   │   ├── task-list-table.tsx      # Table view
│   │   │   ├── create-task-dialog.tsx
│   │   │   ├── task-filters.tsx
│   │   │   ├── label-picker.tsx
│   │   │   ├── label-badge.tsx
│   │   │   ├── priority-icon.tsx
│   │   │   └── assignee-picker.tsx
│   │   │
│   │   ├── comments/
│   │   │   ├── comment-thread.tsx
│   │   │   ├── comment-card.tsx
│   │   │   └── comment-form.tsx
│   │   │
│   │   ├── audit/
│   │   │   ├── audit-timeline.tsx
│   │   │   └── audit-filters.tsx
│   │   │
│   │   └── shared/
│   │       ├── empty-state.tsx
│   │       ├── loading-skeleton.tsx
│   │       ├── confirm-dialog.tsx
│   │       ├── data-table.tsx           # Generic table wrapper
│   │       └── pagination.tsx
│   │
│   ├── hooks/                           # TanStack Query hooks (1 per domain)
│   │   ├── use-auth.ts
│   │   ├── use-orgs.ts
│   │   ├── use-members.ts
│   │   ├── use-invites.ts
│   │   ├── use-projects.ts
│   │   ├── use-tasks.ts
│   │   ├── use-comments.ts
│   │   └── use-audit-logs.ts
│   │
│   ├── lib/
│   │   ├── api-client.ts            # ky instance + interceptors
│   │   ├── auth.ts                  # cookie helpers, token refresh logic
│   │   ├── query-keys.ts            # All TanStack Query key factories
│   │   └── utils.ts                 # cn(), formatDate(), formatRelative()
│   │
│   ├── store/
│   │   └── app-store.ts             # Zustand: user, activeOrg, activeMembership
│   │
│   ├── types/                       # 1:1 mirrors of Pydantic response models
│   │   ├── auth.ts
│   │   ├── org.ts
│   │   ├── project.ts
│   │   ├── task.ts
│   │   ├── comment.ts
│   │   └── audit.ts
│   │
│   ├── validations/                 # Zod schemas — exact mirror of backend rules
│   │   ├── auth.schema.ts
│   │   ├── org.schema.ts
│   │   ├── project.schema.ts
│   │   ├── task.schema.ts
│   │   └── comment.schema.ts
│   │
│   └── providers/
│       ├── query-provider.tsx       # TanStack QueryClientProvider
│       └── theme-provider.tsx       # Dark/light mode context
│
├── index.html
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── components.json                  # shadcn/ui config
├── .env.local
└── package.json
```

---

## Auth Architecture

### Strategy: httpOnly Cookies via Vite Proxy

Because the app is a pure Vite SPA (no Next.js server), we use Vite's dev proxy
to forward `/api/*` requests to the FastAPI backend. In production, nginx handles this.

```
Browser → Vite Proxy (/api/*) → FastAPI (localhost:8000)
```

### Cookie Flow

```
1. User submits login form
   → POST /api/v1/auth/login { email, password }
   → Backend returns { access_token, refresh_token, expires_in }
   → Frontend stores tokens in httpOnly cookies via Set-Cookie
      (configured at nginx/proxy level in production)
   → In development: tokens stored in memory (Zustand) + sessionStorage fallback

2. Every API request
   → api-client.ts reads token from store
   → Attaches: Authorization: Bearer <access_token>

3. On 401 response (token expired)
   → api-client.ts interceptor auto-calls POST /auth/refresh
   → Stores new access_token
   → Retries original request once

4. On logout
   → POST /api/v1/auth/logout { refresh_token }
   → Clear all tokens from store
   → Redirect to /login
```

### Protected Route Guard

```tsx
// src/components/shared/auth-guard.tsx
// Wraps the dashboard layout — redirects to /login if no user in store
```

---

## State Management

### Two-Layer Strategy

```
TanStack Query (server state)          Zustand (client/UI state)
─────────────────────────────          ──────────────────────────
• All API data (orgs, tasks, etc.)     • Authenticated user object
• Caching + background refetch         • Active org + membership
• Mutations + optimistic updates       • Sidebar open/closed
• Pagination                           • Theme (dark/light)
• Invalidation on mutations            • Task detail panel open + taskId
```

### TanStack Query Key Factories

```typescript
// src/lib/query-keys.ts
export const queryKeys = {
  user:        () => ["user"] as const,
  orgs:        () => ["orgs"] as const,
  org:         (orgId: string) => ["org", orgId] as const,
  members:     (orgId: string) => ["org", orgId, "members"] as const,
  invites:     (orgId: string) => ["org", orgId, "invites"] as const,
  projects:    (orgId: string) => ["org", orgId, "projects"] as const,
  project:     (orgId: string, projectId: string) =>
                 ["org", orgId, "project", projectId] as const,
  tasks:       (orgId: string, projectId: string, filters?: TaskFilters) =>
                 ["org", orgId, "project", projectId, "tasks", filters] as const,
  task:        (orgId: string, taskId: string) =>
                 ["org", orgId, "task", taskId] as const,
  comments:    (orgId: string, taskId: string) =>
                 ["org", orgId, "task", taskId, "comments"] as const,
  auditLogs:   (orgId: string, filters?: AuditFilters) =>
                 ["org", orgId, "audit-logs", filters] as const,
}
```

### Mutation Invalidation Rules

```
createOrg       → invalidate: ["orgs"]
updateOrg       → invalidate: ["org", orgId], ["orgs"]
createProject   → invalidate: ["org", orgId, "projects"]
updateProject   → invalidate: project key + projects list
deleteProject   → invalidate: projects list
createTask      → invalidate: tasks list for that project
updateTask      → invalidate: task key + tasks list (optimistic update for status drag)
deleteTask      → invalidate: tasks list
addLabel        → invalidate: task key
removeLabel     → invalidate: task key
createComment   → invalidate: comments key
updateComment   → invalidate: comments key
deleteComment   → invalidate: comments key
inviteMember    → invalidate: invites key
```

---

## API Client Layer

```typescript
// src/lib/api-client.ts

import ky from "ky"
import { useAppStore } from "@/store/app-store"

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"

export const apiClient = ky.create({
  prefixUrl: `${BASE_URL}/api/v1`,
  hooks: {
    beforeRequest: [
      (request) => {
        const token = useAppStore.getState().accessToken
        if (token) {
          request.headers.set("Authorization", `Bearer ${token}`)
        }
      },
    ],
    afterResponse: [
      async (request, options, response) => {
        if (response.status === 401) {
          // Auto-refresh and retry once
          const refreshed = await refreshTokens()
          if (refreshed) {
            return ky(request)
          }
          useAppStore.getState().logout()
          window.location.href = "/login"
        }
      },
    ],
  },
})
```

---

## RBAC on the Frontend

### Role Hierarchy (mirrors backend)

```typescript
// src/types/org.ts
export type OrgRole = "owner" | "admin" | "member" | "viewer"

const ROLE_RANK: Record<OrgRole, number> = {
  viewer: 0,
  member: 1,
  admin:  2,
  owner:  3,
}

export function hasRole(userRole: OrgRole, required: OrgRole): boolean {
  return ROLE_RANK[userRole] >= ROLE_RANK[required]
}
```

### Usage in Components

```tsx
const { activeMembership } = useAppStore()

// Hide "Create Project" button for VIEWER
{hasRole(activeMembership.role, "member") && (
  <Button onClick={() => setCreateOpen(true)}>New Project</Button>
)}

// Sidebar nav items — conditionally rendered
{hasRole(activeMembership.role, "admin") && (
  <>
    <NavItem to="invites">Invites</NavItem>
    <NavItem to="audit-logs">Audit Logs</NavItem>
  </>
)}
{hasRole(activeMembership.role, "owner") && (
  <NavItem to="settings">Settings</NavItem>
)}
```

### RBAC Visibility Matrix

| UI Element | VIEWER | MEMBER | ADMIN | OWNER |
|---|---|---|---|---|
| View projects / tasks / comments | ✅ | ✅ | ✅ | ✅ |
| Create task / comment / label | ❌ | ✅ | ✅ | ✅ |
| Create project | ❌ | ✅ | ✅ | ✅ |
| Edit / delete any task | ❌ | ❌ | ✅ | ✅ |
| Delete task (soft) | ❌ | ❌ | ✅ | ✅ |
| Invite members | ❌ | ❌ | ✅ | ✅ |
| Change member roles | ❌ | ❌ | ✅ | ✅ |
| Remove members | ❌ | ❌ | ✅ | ✅ |
| View Audit Logs | ❌ | ❌ | ✅ | ✅ |
| Edit org settings | ❌ | ❌ | ❌ | ✅ |

> **Note:** Frontend RBAC is UI-only (hides buttons, disables actions).
> The backend enforces all role checks — the frontend is never the last line of defence.

---

## Routing Strategy

### Route Tree (React Router v7)

```
/                           → redirect → /orgs
/login                      → auth-layout + LoginPage
/register                   → auth-layout + RegisterPage
/invite/:token              → auth-layout + AcceptInvitePage

/orgs                       → dashboard-layout
  /                         → OrgListPage
  /:orgId                   → OrgDashboardPage
    /settings               → OrgSettingsPage       (owner only)
    /members                → MembersPage           (any member)
    /invites                → InvitesPage           (admin+)
    /audit-logs             → AuditLogsPage         (admin+)
    /projects               → ProjectListPage
      /:projectId           → redirect → .../board
        /board              → KanbanBoardPage
        /list               → TaskListPage
        /settings           → ProjectSettingsPage   (admin+)
```

---

## Component Architecture

### Design Principles

1. **Pages** are thin — they just compose components and pass data down
2. **Hooks** own all API logic — no `fetch` calls inside components
3. **Components** receive typed props, never call `useQuery` directly (except smart/container components)
4. **UI components** are pure shadcn/ui primitives — no business logic

### Task Detail Panel (most complex component)

```
TaskDetailPanel (Sheet/SlideOver)
  ├── TaskHeader
  │   ├── Title (inline editable)
  │   ├── StatusSelect
  │   ├── PriorityIcon
  │   └── AssigneePicker
  ├── TaskMeta
  │   ├── ProjectBreadcrumb
  │   ├── CreatedAt / UpdatedAt
  │   └── LabelList
  │       └── LabelBadge × n
  │           └── RemoveLabelButton
  ├── LabelPicker (Add label)
  ├── TaskDescription (inline editable textarea)
  ├── Divider
  └── CommentThread
      ├── CommentCard × n
      │   ├── AuthorAvatar
      │   ├── CommentBody (inline editable for author/admin)
      │   ├── EditButton (author or admin only)
      │   └── DeleteButton (author or admin only)
      └── CommentForm
          └── Textarea + Submit
```

---

## Form Validation Strategy

### Zod schemas mirror backend Pydantic rules exactly

```typescript
// src/validations/auth.schema.ts
import { z } from "zod"

const SPECIAL_RE = /[!@#$%^&*()\-_=+\[\]{};:'",.<>/?\\|`~]/

export const registerSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z
    .string()
    .min(8, "Minimum 8 characters")
    .max(128, "Maximum 128 characters")
    .refine((v) => /[a-z]/.test(v), "Must contain a lowercase letter")
    .refine((v) => /[A-Z]/.test(v), "Must contain an uppercase letter")
    .refine((v) => /\d/.test(v), "Must contain a digit")
    .refine((v) => SPECIAL_RE.test(v), "Must contain a special character"),
  full_name: z.string().max(255).optional(),
})

// src/validations/org.schema.ts
export const createOrgSchema = z.object({
  name: z.string().min(1).max(255),
  slug: z.string().min(2).max(100).regex(/^[a-z0-9-]+$/, "Lowercase, numbers and hyphens only"),
  description: z.string().max(1000).optional(),
})

// src/validations/task.schema.ts
export const createTaskSchema = z.object({
  title:             z.string().min(1).max(500),
  description:       z.string().max(5000).optional(),
  status:            z.enum(["todo","in_progress","done","blocked"]).default("todo"),
  priority:          z.enum(["low","medium","high","urgent"]).default("medium"),
  assignee_user_id:  z.string().uuid().optional().nullable(),
  position:          z.number().int().min(0).default(0),
})
```

---

## Error Handling

### API Error Response Shape (from backend)

```json
{
  "detail": "Organisation not found."
}
```

### Frontend Error Strategy

```
API Error (4xx / 5xx)
       │
       ▼
 api-client afterResponse hook
       │
       ├── 401 → auto-refresh → retry once → logout if still 401
       ├── 403 → show toast "You don't have permission to do this"
       ├── 404 → show empty state or navigate to not-found
       ├── 409 → surface field-level error (e.g. "Slug already taken")
       ├── 422 → surface Pydantic validation errors to form fields
       ├── 429 → show toast "Too many requests, please wait"
       └── 500 → show toast "Something went wrong" + log request_id
```

---

## Module Plan

| Module | Pages / Features | Priority |
|---|---|---|
| **M-F1: Auth** | Login, Register, Accept Invite, Auth Guard | 🔴 First |
| **M-F2: Organizations** | Org List/Create, Dashboard, Settings, Members, Invites | 🔴 Second |
| **M-F3: Projects** | Project List/Create, Project settings | 🟠 Third |
| **M-F4: Tasks** | Kanban Board, Task List, Task Detail Panel, Labels | 🟠 Fourth |
| **M-F5: Comments** | Thread inside Task Panel, Create/Edit/Delete | 🟡 Fifth |
| **M-F6: Audit Logs** | Timeline, Filters, Pagination | 🟡 Sixth |
| **Polish** | Dark mode, Skeletons, Empty states, Mobile nav, Error boundaries | 🟢 Last |

---

## Environment Variables

```bash
# frontend/.env.local

VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=Tenantrix
VITE_APP_VERSION=0.1.0
```

---

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Framework | Vite + React SPA | No SSR needed, faster dev, simpler deployment |
| Repo layout | Monorepo (`frontend/` inside backend repo) | Single clone, coordinated versioning, shared docs |
| Auth storage | Tokens in Zustand (memory) | httpOnly cookies need server-side proxy; in dev, memory is sufficient. Production: nginx sets httpOnly cookies |
| Token refresh | Automatic via ky interceptor on 401 | Seamless UX — user never sees a logout unless refresh also fails |
| Dark mode | Default dark | Matches Jira/Linear aesthetic preference |
| Component library | shadcn/ui | Accessible, composable, owned code (not a black-box npm package) |
| Drag & drop | @dnd-kit | Accessible, no jQuery dependency, purpose-built for React |
| No Redux | Zustand instead | Redux overkill for this app size; Zustand is 1KB and sufficient |
| Soft delete | Frontend never shows `deleted_at != null` items | Backend already filters these out in list endpoints |
| Pagination | Offset-based "Load more" on audit logs, standard pagination elsewhere | Matches backend `limit/offset` model |
