# Tenantrix Web — Frontend Changelog

All notable changes to the Tenantrix frontend will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Module numbering: `M-F1` through `M-F6` (F = Frontend).

---

## [Unreleased]

---

### M-F1 — Authentication & App Shell

#### Added
- Vite + React 19 + TypeScript project scaffold (`frontend/`)
- Tailwind CSS v4 + shadcn/ui setup (`components.json`, `tailwind.config.ts`)
- Dark mode default via `ThemeProvider`
- React Router v7 route tree with `AuthLayout` and `DashboardLayout`
- `AuthGuard` component — redirects unauthenticated users to `/login`
- `LoginPage` — email/password form → `POST /auth/login`
- `RegisterPage` — email/password/full_name form → `POST /auth/register`
- `AcceptInvitePage` — token-from-URL → `POST /organizations/invites/accept/:token`
- `useLogin`, `useRegister`, `useLogout`, `useCurrentUser` hooks (`hooks/use-auth.ts`)
- `api-client.ts` — ky instance with `beforeRequest` auth header injection
- `api-client.ts` — `afterResponse` 401 interceptor: auto-refresh → retry → logout
- Zustand `app-store.ts` — `user`, `accessToken`, `refreshToken`, `activeOrg`, `activeMembership`, `sidebarOpen`
- `TanStack QueryProvider` and `ThemeProvider` wrappers in `providers/`
- `TopBar` with `UserMenu` (avatar, full name, logout)
- `Sidebar` with org navigation skeleton
- `PasswordStrengthIndicator` component
- Zod schemas: `loginSchema`, `registerSchema` (mirrors backend Pydantic rules)
- TypeScript types: `User`, `TokenResponse` (`types/auth.ts`)
- `query-keys.ts` factory: `queryKeys.user()`
- `vite.config.ts` — dev proxy: `/api/* → http://localhost:8000`
- `.env.local` with `VITE_API_BASE_URL`, `VITE_APP_NAME`, `VITE_APP_VERSION`

#### Implementation Notes
- Token storage: `accessToken` and `refreshToken` in Zustand (in-memory). On page reload, `useCurrentUser` re-validates session via `GET /auth/me`; if 401, user is redirected to `/login`.
- In production, nginx sits in front of Vite's built output and proxies `/api/*` — enabling httpOnly `Set-Cookie` behaviour.
- `api-client.ts` uses a `isRefreshing` flag + a pending request queue to prevent concurrent token refresh storms.

---

### M-F2 — Organizations, Members & Invites

#### Added
- `OrgListPage` (`/orgs`) — list of orgs current user belongs to, `CreateOrgDialog`
- `OrgDashboardPage` (`/orgs/:orgId`) — org overview, recent activity
- `OrgSettingsPage` (`/orgs/:orgId/settings`) — name/slug/description edit (owner only), delete org
- `MembersPage` (`/orgs/:orgId/members`) — member table with inline role change, remove member
- `InvitesPage` (`/orgs/:orgId/invites`) — list pending invites, create invite dialog (admin+)
- `OrgSwitcher` in sidebar — dropdown of all user orgs, sets `activeOrg` in Zustand
- `OrgCard` component for org list
- `MemberTable` — sortable table, role badge, inline role select, remove button
- `InviteDialog` — email + role picker → `POST /organizations/:orgId/invites`
- `InviteList` — pending invites with status badge and revoke button
- `RoleBadge` component — colour-coded: owner=purple, admin=blue, member=green, viewer=gray
- `ConfirmDialog` shared component — used for delete/remove destructive actions
- Hooks: `useOrgs`, `useOrg`, `useCreateOrg`, `useUpdateOrg`, `useDeleteOrg`
- Hooks: `useMembers`, `useUpdateMemberRole`, `useRemoveMember`
- Hooks: `useInvites`, `useCreateInvite`, `useAcceptInvite`
- Zod schemas: `createOrgSchema`, `updateOrgSchema`, `createInviteSchema`
- TypeScript types: `Organization`, `Member`, `Invite`, `OrgRole` (`types/org.ts`)
- `hasRole(userRole, required)` utility — RBAC gate function
- `query-keys.ts` extended: `orgs`, `org`, `members`, `invites`
- RBAC enforcement: all destructive/admin actions guarded by `hasRole()` checks

#### Implementation Notes
- Active org stored in `app-store.ts`. On org switch, all org-scoped queries are invalidated.
- `activeMembership` (user's role in `activeOrg`) is derived from `useMembers` and stored in Zustand on org switch.
- `OrgSettingsPage` is only reachable via sidebar link which is only rendered for `role === "owner"`. Route is not otherwise protected — backend enforces the 403.

---

### M-F3 — Projects

#### Added
- `ProjectListPage` (`/orgs/:orgId/projects`) — project grid/list, `CreateProjectDialog`
- `ProjectSettingsPage` (`/orgs/:orgId/projects/:id/settings`) — name/description/status edit, delete project (admin+)
- `ProjectCard` — status badge, task count (future), quick-navigate to board
- `CreateProjectDialog` — name + description + status → `POST /organizations/:orgId/projects`
- `ProjectStatusBadge` — active=green, archived=gray
- Hooks: `useProjects`, `useProject`, `useCreateProject`, `useUpdateProject`, `useDeleteProject`
- Zod schemas: `createProjectSchema`, `updateProjectSchema`
- TypeScript type: `Project` (`types/project.ts`)
- `query-keys.ts` extended: `projects`, `project`
- View toggle: grid view ↔ list view (stored in `app-store.ts`)

#### Implementation Notes
- Navigating to `/orgs/:orgId/projects/:id` auto-redirects to `.../board`.
- Archived projects are visually dimmed in the list but still navigable.

---

### M-F4 — Tasks, Kanban Board & Labels

#### Added
- `KanbanBoardPage` (`/…/projects/:id/board`) — 4-column board (Todo, In Progress, Done, Blocked)
- `TaskListPage` (`/…/projects/:id/list`) — flat table view with sortable columns
- `TaskDetailPanel` — shadcn `Sheet` slide-over, opens on task card click
- `TaskCard` — draggable card (dnd-kit `useSortable`), priority icon, assignee avatar, label badges
- `KanbanColumn` — `SortableContext` wrapper, "Add task" button at bottom
- `CreateTaskDialog` — title, description, status, priority, assignee, position
- `TaskFilters` — filter bar: status, priority, assignee, label (updates query key → refetches)
- `LabelPicker` — popover with existing labels + create-new; filters out already-applied labels
- `LabelBadge` — coloured badge with × remove button
- `PriorityIcon` — icons + colours: urgent=red, high=orange, medium=yellow, low=gray
- `AssigneePicker` — member search dropdown, shows avatar + name
- Drag-and-drop: cross-column drag updates `task.status` via `PATCH` with optimistic update; reverts on error
- Hooks: `useTasks`, `useTask`, `useCreateTask`, `useUpdateTask`, `useDeleteTask`
- Hooks: `useAddLabel`, `useRemoveLabel`
- Zod schemas: `createTaskSchema`, `updateTaskSchema`
- TypeScript types: `Task`, `TaskStatus`, `TaskPriority`, `Label`, `TaskFilters` (`types/task.ts`)
- `query-keys.ts` extended: `tasks`, `task`
- `LoadingSkeleton` variants for kanban column and task list table

#### Implementation Notes
- Kanban drag uses `DndContext` with `closestCorners` collision detection strategy.
- On drag end: `onDragEnd` handler reads `over.id` (column status) and fires `useUpdateTask` with `{ status: newStatus, position: newPosition }`.
- Optimistic update: `queryClient.setQueryData` moves card immediately in the tasks array; `onError` callback calls `queryClient.invalidateQueries` to restore server state.
- `TaskDetailPanel` opens by setting `{ taskPanelOpen: true, activetaskId: taskId }` in Zustand.

---

### M-F5 — Comments

#### Added
- `CommentThread` — scrollable list of comments inside `TaskDetailPanel`
- `CommentCard` — author avatar, name, relative timestamp, body; edit/delete controls for author or admin
- `CommentForm` — textarea + submit button; disabled for VIEWER role
- Inline edit mode: clicking "Edit" on a `CommentCard` replaces body with textarea
- `useComments`, `useCreateComment`, `useUpdateComment`, `useDeleteComment` hooks
- Zod schema: `createCommentSchema`, `updateCommentSchema`
- TypeScript type: `Comment` (`types/comment.ts`)
- `query-keys.ts` extended: `comments`
- RBAC: edit/delete button on own comments visible for `member+`; visible on any comment for `admin+`

#### Implementation Notes
- `staleTime` for comments is 30s (more frequent activity than other resources).
- Comment list re-fetches automatically when `TaskDetailPanel` is opened.
- Author avatar is a coloured initials circle (no separate avatar upload required).

---

### M-F6 — Audit Logs

#### Added
- `AuditLogsPage` (`/orgs/:orgId/audit-logs`) — accessible to `admin+` only
- `AuditTimeline` — vertically stacked event timeline with icon per action type
- `AuditFilters` — filter by actor, action type, resource type; date range picker
- `LoadMore` button — offset-based pagination (`limit=50`)
- `useAuditLogs(orgId, filters?)` hook
- TypeScript type: `AuditLog`, `AuditFilters` (`types/audit.ts`)
- `query-keys.ts` extended: `auditLogs`
- Action-to-icon mapping: `task.*` → CheckSquare, `member.*` → Users, `project.*` → FolderKanban, `org.*` → Building2
- `EmptyState` component shown when no audit logs match filters

#### Implementation Notes
- Audit logs are append-only — no mutations, only reads.
- Sidebar nav item only rendered for `hasRole(role, "admin")`.
- Filter state is stored in component local state (not Zustand) and passed to `useAuditLogs`.
- `metadata` field is rendered as a human-readable sentence using an `actionToSentence()` helper.

---

### Polish & Cross-Cutting

#### Added
- Error boundaries (`ErrorBoundary`) at route level — shows friendly error card on unhandled JS errors
- `EmptyState` component — illustration + message for empty lists/searches
- `LoadingSkeleton` — per-component skeleton loaders (not full-page spinners)
- `Pagination` shared component for table views
- `DataTable` generic component — sortable columns, row selection
- Mobile responsive sidebar — `Sheet` drawer on `< lg` viewports
- `Breadcrumb` navigation in `TopBar` — updates on route change
- Toast notifications via Sonner — success, error, and info variants
- `ThemeToggle` button in `TopBar` — dark ↔ light mode toggle
- `NotFoundPage` — custom 404 page
- Keyboard shortcut `Cmd/Ctrl + K` — opens org/project/task quick-search (future)

---

## Versioning Strategy

Frontend versioning mirrors backend module numbering:

| Version | Backend | Frontend |
|---|---|---|
| `0.1.x` | M1–M9 complete | Not started |
| `0.2.0` | — | M-F1 (Auth + App Shell) |
| `0.3.0` | — | M-F2 (Organizations) |
| `0.4.0` | — | M-F3 (Projects) |
| `0.5.0` | — | M-F4 (Tasks + Kanban) |
| `0.6.0` | — | M-F5 (Comments) |
| `0.7.0` | — | M-F6 (Audit Logs) |
| `0.8.0` | — | Polish + Bug fixes |
| `1.0.0` | Both | Full release |
