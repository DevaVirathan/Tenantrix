# Tenantrix Web — Frontend API Reference

> Maps every backend endpoint to its corresponding frontend hook, component,
> TypeScript type, Zod schema, TanStack Query key, and error handling.

Backend base URL: `http://localhost:8000/api/v1`

---

## Table of Contents

- [Auth](#auth)
- [Organizations](#organizations)
- [Members](#members)
- [Invites](#invites)
- [Projects](#projects)
- [Tasks](#tasks)
- [Labels](#labels)
- [Comments](#comments)
- [Audit Logs](#audit-logs)
- [Health](#health)
- [TypeScript Types Reference](#typescript-types-reference)

---

## Auth

### POST /auth/register

| Field | Value |
|---|---|
| **Hook** | `useRegister()` in `hooks/use-auth.ts` |
| **Component** | `RegisterForm` |
| **Page** | `/register` |
| **Mutation key** | `["auth", "register"]` |
| **Zod schema** | `registerSchema` |
| **On success** | Navigate to `/orgs`, set user in Zustand store |
| **On 409** | Toast "Email already registered" |

**Request body**
```json
{
  "email": "user@example.com",
  "password": "SecurePass1!",
  "full_name": "Jane Smith"
}
```

**Response** `201`
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900
}
```

---

### POST /auth/login

| Field | Value |
|---|---|
| **Hook** | `useLogin()` in `hooks/use-auth.ts` |
| **Component** | `LoginForm` |
| **Page** | `/login` |
| **Mutation key** | `["auth", "login"]` |
| **Zod schema** | `loginSchema` |
| **On success** | Store tokens in Zustand, navigate to `/orgs` |
| **On 401** | Toast "Invalid email or password" |

**Request body** (`application/x-www-form-urlencoded`)
```
username=user@example.com&password=SecurePass1!&grant_type=password
```

**Response** `200`
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900
}
```

---

### POST /auth/refresh

| Field | Value |
|---|---|
| **Hook** | Called automatically by `api-client.ts` interceptor |
| **Component** | Transparent — no UI |
| **Trigger** | Any 401 response from any API call |
| **On success** | New token stored in Zustand, original request retried |
| **On failure** | Logout + redirect to `/login` |

**Request body**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response** `200`
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900
}
```

---

### POST /auth/logout

| Field | Value |
|---|---|
| **Hook** | `useLogout()` in `hooks/use-auth.ts` |
| **Component** | `UserMenu` (avatar dropdown) |
| **On success** | Clear Zustand store, navigate to `/login` |

**Request body**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response** `204 No Content`

---

### GET /auth/me

| Field | Value |
|---|---|
| **Hook** | `useCurrentUser()` in `hooks/use-auth.ts` |
| **Query key** | `["user"]` |
| **Component** | `TopBar` → `UserMenu` |
| **Purpose** | Verify session on app boot; populate user in Zustand |
| **On 401** | Redirect to `/login` |

**Response** `200`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "Jane Smith",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z"
}
```

---

## Organizations

### GET /organizations

| Field | Value |
|---|---|
| **Hook** | `useOrgs()` in `hooks/use-orgs.ts` |
| **Query key** | `["orgs"]` |
| **Component** | `OrgListPage` → `OrgCard × n` |
| **staleTime** | 5 minutes |

**Response** `200`
```json
[
  {
    "id": "uuid",
    "name": "Acme Corp",
    "slug": "acme-corp",
    "description": "...",
    "created_at": "...",
    "updated_at": "..."
  }
]
```

---

### POST /organizations

| Field | Value |
|---|---|
| **Hook** | `useCreateOrg()` in `hooks/use-orgs.ts` |
| **Component** | `CreateOrgDialog` |
| **Zod schema** | `createOrgSchema` |
| **On success** | Invalidate `["orgs"]`, close dialog, navigate to `/orgs/:newId` |
| **On 409** | Form error "Slug already taken" |

**Request body**
```json
{
  "name": "Acme Corp",
  "slug": "acme-corp",
  "description": "Optional description"
}
```

**Response** `201` — full `Organization` object

---

### GET /organizations/:orgId

| Field | Value |
|---|---|
| **Hook** | `useOrg(orgId)` in `hooks/use-orgs.ts` |
| **Query key** | `["org", orgId]` |
| **Component** | `OrgDashboardPage`, `OrgSettingsPage` |
| **On 404** | Navigate to `/orgs` + toast "Organisation not found" |

**Response** `200` — full `Organization` object

---

### PATCH /organizations/:orgId

| Field | Value |
|---|---|
| **Hook** | `useUpdateOrg(orgId)` in `hooks/use-orgs.ts` |
| **Component** | `OrgSettingsPage` (inline edit form) |
| **Zod schema** | `updateOrgSchema` (all fields optional) |
| **RBAC** | Render form only if `role === "owner"` |
| **On success** | Invalidate `["org", orgId]` and `["orgs"]` |
| **On 409** | Form error "Slug already taken" |

**Request body** (all fields optional)
```json
{
  "name": "New Name",
  "slug": "new-slug",
  "description": "Updated description"
}
```

**Response** `200` — updated `Organization` object

---

### DELETE /organizations/:orgId

| Field | Value |
|---|---|
| **Hook** | `useDeleteOrg(orgId)` in `hooks/use-orgs.ts` |
| **Component** | `OrgSettingsPage` → `ConfirmDialog` |
| **RBAC** | Visible only if `role === "owner"` |
| **On success** | Invalidate `["orgs"]`, navigate to `/orgs` |
| **On 400** | Toast "Cannot delete: active projects exist" |

**Response** `204 No Content`

---

## Members

### GET /organizations/:orgId/members

| Field | Value |
|---|---|
| **Hook** | `useMembers(orgId)` in `hooks/use-members.ts` |
| **Query key** | `["org", orgId, "members"]` |
| **Component** | `MembersPage` → `MemberTable` |

**Response** `200`
```json
[
  {
    "user_id": "uuid",
    "email": "user@example.com",
    "full_name": "Jane Smith",
    "role": "admin",
    "joined_at": "2025-01-01T00:00:00Z"
  }
]
```

---

### PATCH /organizations/:orgId/members/:userId

| Field | Value |
|---|---|
| **Hook** | `useUpdateMemberRole(orgId)` in `hooks/use-members.ts` |
| **Component** | `MemberTable` → role dropdown (inline) |
| **RBAC** | Visible only if `role === "admin"` or `"owner"` |
| **On success** | Invalidate `["org", orgId, "members"]` |
| **On 403** | Toast "Cannot demote the only owner" |

**Request body**
```json
{
  "role": "member"
}
```

**Response** `200` — updated `Member` object

---

### DELETE /organizations/:orgId/members/:userId

| Field | Value |
|---|---|
| **Hook** | `useRemoveMember(orgId)` in `hooks/use-members.ts` |
| **Component** | `MemberTable` → `ConfirmDialog` |
| **RBAC** | Button visible only if `role === "admin"` or `"owner"` |
| **On success** | Invalidate `["org", orgId, "members"]` |

**Response** `204 No Content`

---

## Invites

### POST /organizations/:orgId/invites

| Field | Value |
|---|---|
| **Hook** | `useCreateInvite(orgId)` in `hooks/use-invites.ts` |
| **Component** | `InvitesPage` → `InviteDialog` |
| **Zod schema** | `createInviteSchema` |
| **RBAC** | Form visible only if `role === "admin"` or `"owner"` |
| **On success** | Invalidate `["org", orgId, "invites"]`, show invite link in toast |
| **On 409** | Toast "User already a member or already invited" |

**Request body**
```json
{
  "invitee_email": "newuser@example.com",
  "role": "member"
}
```

**Response** `201`
```json
{
  "id": "uuid",
  "token": "abc123...",
  "invitee_email": "newuser@example.com",
  "role": "member",
  "expires_at": "2025-02-01T00:00:00Z",
  "status": "pending"
}
```

---

### GET /organizations/:orgId/invites

| Field | Value |
|---|---|
| **Hook** | `useInvites(orgId)` in `hooks/use-invites.ts` |
| **Query key** | `["org", orgId, "invites"]` |
| **Component** | `InvitesPage` → `InviteList` |
| **RBAC** | Page accessible only if `role === "admin"` or `"owner"` |

**Response** `200` — array of `Invite` objects

---

### POST /organizations/invites/accept/:token

| Field | Value |
|---|---|
| **Hook** | `useAcceptInvite()` in `hooks/use-invites.ts` |
| **Component** | `AcceptInvitePage` |
| **Page** | `/invite/:token` |
| **On success** | Navigate to `/orgs/:orgId` |
| **On 400** | Toast "Invite expired or already used" |
| **On 404** | Toast "Invite not found" |

**Response** `200`
```json
{
  "message": "Successfully joined organisation.",
  "organisation_id": "uuid"
}
```

---

## Projects

### GET /organizations/:orgId/projects

| Field | Value |
|---|---|
| **Hook** | `useProjects(orgId)` in `hooks/use-projects.ts` |
| **Query key** | `["org", orgId, "projects"]` |
| **Component** | `ProjectListPage` → `ProjectCard × n` |
| **staleTime** | 3 minutes |

**Response** `200`
```json
[
  {
    "id": "uuid",
    "organisation_id": "uuid",
    "name": "Website Redesign",
    "description": "...",
    "status": "active",
    "created_at": "...",
    "updated_at": "..."
  }
]
```

---

### POST /organizations/:orgId/projects

| Field | Value |
|---|---|
| **Hook** | `useCreateProject(orgId)` in `hooks/use-projects.ts` |
| **Component** | `ProjectListPage` → `CreateProjectDialog` |
| **Zod schema** | `createProjectSchema` |
| **RBAC** | Button visible if `hasRole(role, "member")` |
| **On success** | Invalidate `["org", orgId, "projects"]`, navigate to board |

**Request body**
```json
{
  "name": "Website Redesign",
  "description": "Optional project description",
  "status": "active"
}
```

**Response** `201` — full `Project` object

---

### GET /organizations/:orgId/projects/:projectId

| Field | Value |
|---|---|
| **Hook** | `useProject(orgId, projectId)` in `hooks/use-projects.ts` |
| **Query key** | `["org", orgId, "project", projectId]` |
| **Component** | `KanbanBoardPage`, `TaskListPage`, `ProjectSettingsPage` |

**Response** `200` — full `Project` object

---

### PATCH /organizations/:orgId/projects/:projectId

| Field | Value |
|---|---|
| **Hook** | `useUpdateProject(orgId, projectId)` in `hooks/use-projects.ts` |
| **Component** | `ProjectSettingsPage` |
| **RBAC** | Form visible if `hasRole(role, "admin")` |
| **On success** | Invalidate project key + projects list |

**Request body** (all fields optional)
```json
{
  "name": "New Name",
  "description": "Updated",
  "status": "archived"
}
```

**Response** `200` — updated `Project` object

---

### DELETE /organizations/:orgId/projects/:projectId

| Field | Value |
|---|---|
| **Hook** | `useDeleteProject(orgId, projectId)` in `hooks/use-projects.ts` |
| **Component** | `ProjectSettingsPage` → `ConfirmDialog` |
| **RBAC** | Button visible if `hasRole(role, "admin")` |
| **On success** | Invalidate projects list, navigate to `/orgs/:orgId/projects` |

**Response** `204 No Content`

---

## Tasks

### GET /organizations/:orgId/projects/:projectId/tasks

| Field | Value |
|---|---|
| **Hook** | `useTasks(orgId, projectId, filters?)` in `hooks/use-tasks.ts` |
| **Query key** | `["org", orgId, "project", projectId, "tasks", filters]` |
| **Component** | `KanbanBoardPage` (grouped by status), `TaskListPage` (flat table) |
| **staleTime** | 1 minute |

**Query params (all optional)**
```
status=todo|in_progress|done|blocked
priority=low|medium|high|urgent
assignee_user_id=<uuid>
label_id=<uuid>
limit=50
offset=0
```

**Response** `200`
```json
[
  {
    "id": "uuid",
    "project_id": "uuid",
    "title": "Design mockups",
    "description": "...",
    "status": "todo",
    "priority": "high",
    "position": 0,
    "assignee_user_id": "uuid",
    "created_by_user_id": "uuid",
    "created_at": "...",
    "updated_at": "...",
    "deleted_at": null,
    "labels": []
  }
]
```

---

### POST /organizations/:orgId/projects/:projectId/tasks

| Field | Value |
|---|---|
| **Hook** | `useCreateTask(orgId, projectId)` in `hooks/use-tasks.ts` |
| **Component** | `KanbanColumn` → `CreateTaskDialog`, `TaskListPage` → `CreateTaskDialog` |
| **Zod schema** | `createTaskSchema` |
| **RBAC** | Button visible if `hasRole(role, "member")` |
| **On success** | Invalidate tasks list |

**Request body**
```json
{
  "title": "Design mockups",
  "description": "Create high-fidelity mockups for homepage",
  "status": "todo",
  "priority": "high",
  "assignee_user_id": null,
  "position": 0
}
```

**Response** `201` — full `Task` object (with empty `labels: []`)

---

### GET /organizations/:orgId/projects/:projectId/tasks/:taskId

| Field | Value |
|---|---|
| **Hook** | `useTask(orgId, taskId)` in `hooks/use-tasks.ts` |
| **Query key** | `["org", orgId, "task", taskId]` |
| **Component** | `TaskDetailPanel` (slide-over) |
| **Trigger** | Click on `TaskCard` anywhere |

**Response** `200` — full `Task` object with `labels` array populated

---

### PATCH /organizations/:orgId/projects/:projectId/tasks/:taskId

| Field | Value |
|---|---|
| **Hook** | `useUpdateTask(orgId, projectId, taskId)` in `hooks/use-tasks.ts` |
| **Component** | `TaskDetailPanel` (inline edit), `KanbanBoard` (drag = status change) |
| **Zod schema** | `updateTaskSchema` (all fields optional) |
| **RBAC** | Edit controls visible if `hasRole(role, "member")` (own tasks) or `"admin"` (any task) |
| **On success** | Invalidate `["org", orgId, "task", taskId]` and tasks list |
| **Optimistic update** | Kanban drag immediately moves card; reverts on error |

**Request body** (all fields optional)
```json
{
  "title": "Updated title",
  "status": "in_progress",
  "priority": "urgent",
  "assignee_user_id": "uuid",
  "position": 2
}
```

**Response** `200` — updated `Task` object

---

### DELETE /organizations/:orgId/projects/:projectId/tasks/:taskId

| Field | Value |
|---|---|
| **Hook** | `useDeleteTask(orgId, projectId, taskId)` in `hooks/use-tasks.ts` |
| **Component** | `TaskDetailPanel` → `ConfirmDialog` (3-dot menu) |
| **RBAC** | Button visible if `hasRole(role, "admin")` |
| **On success** | Invalidate tasks list, close panel |

**Response** `204 No Content`

---

## Labels

### POST /organizations/:orgId/projects/:projectId/tasks/:taskId/labels

| Field | Value |
|---|---|
| **Hook** | `useAddLabel(orgId, projectId, taskId)` in `hooks/use-tasks.ts` |
| **Component** | `TaskDetailPanel` → `LabelPicker` |
| **RBAC** | Visible if `hasRole(role, "member")` |
| **On success** | Invalidate `["org", orgId, "task", taskId]` |
| **On 409** | Label already applied — no-op (picker filters out existing labels) |

**Request body**
```json
{
  "name": "bug",
  "color": "#ef4444"
}
```

**Response** `201`
```json
{
  "id": "uuid",
  "name": "bug",
  "color": "#ef4444"
}
```

---

### DELETE /organizations/:orgId/projects/:projectId/tasks/:taskId/labels/:labelId

| Field | Value |
|---|---|
| **Hook** | `useRemoveLabel(orgId, projectId, taskId)` in `hooks/use-tasks.ts` |
| **Component** | `TaskDetailPanel` → `LabelBadge` → × button |
| **RBAC** | Visible if `hasRole(role, "member")` |
| **On success** | Invalidate `["org", orgId, "task", taskId]` |

**Response** `204 No Content`

---

## Comments

### GET /organizations/:orgId/projects/:projectId/tasks/:taskId/comments

| Field | Value |
|---|---|
| **Hook** | `useComments(orgId, taskId)` in `hooks/use-comments.ts` |
| **Query key** | `["org", orgId, "task", taskId, "comments"]` |
| **Component** | `TaskDetailPanel` → `CommentThread` |
| **staleTime** | 30 seconds (comments are frequent) |

**Response** `200`
```json
[
  {
    "id": "uuid",
    "task_id": "uuid",
    "author_user_id": "uuid",
    "author_email": "user@example.com",
    "author_full_name": "Jane Smith",
    "body": "This needs a review first.",
    "created_at": "...",
    "updated_at": "..."
  }
]
```

---

### POST /organizations/:orgId/projects/:projectId/tasks/:taskId/comments

| Field | Value |
|---|---|
| **Hook** | `useCreateComment(orgId, projectId, taskId)` in `hooks/use-comments.ts` |
| **Component** | `CommentForm` (at bottom of CommentThread) |
| **Zod schema** | `createCommentSchema` |
| **RBAC** | Form visible if `hasRole(role, "member")` |
| **On success** | Invalidate `["org", orgId, "task", taskId, "comments"]`, clear form |

**Request body**
```json
{
  "body": "This needs a review first."
}
```

**Response** `201` — full `Comment` object

---

### PATCH /organizations/:orgId/projects/:projectId/tasks/:taskId/comments/:commentId

| Field | Value |
|---|---|
| **Hook** | `useUpdateComment(orgId, projectId, taskId)` in `hooks/use-comments.ts` |
| **Component** | `CommentCard` → inline edit mode |
| **RBAC** | Edit button visible if `userId === comment.author_user_id` or `hasRole(role, "admin")` |
| **On success** | Invalidate comments key |

**Request body**
```json
{
  "body": "Updated comment text"
}
```

**Response** `200` — updated `Comment` object

---

### DELETE /organizations/:orgId/projects/:projectId/tasks/:taskId/comments/:commentId

| Field | Value |
|---|---|
| **Hook** | `useDeleteComment(orgId, projectId, taskId)` in `hooks/use-comments.ts` |
| **Component** | `CommentCard` → delete button |
| **RBAC** | Delete button visible if `userId === comment.author_user_id` or `hasRole(role, "admin")` |
| **On success** | Invalidate comments key |

**Response** `204 No Content`

---

## Audit Logs

### GET /organizations/:orgId/audit-logs

| Field | Value |
|---|---|
| **Hook** | `useAuditLogs(orgId, filters?)` in `hooks/use-audit-logs.ts` |
| **Query key** | `["org", orgId, "audit-logs", filters]` |
| **Component** | `AuditLogsPage` → `AuditTimeline` |
| **RBAC** | Page accessible only if `hasRole(role, "admin")` |
| **Pagination** | Offset-based "Load more" |

**Query params (all optional)**
```
actor_user_id=<uuid>
action=<string>      e.g. "task.created", "member.role_changed"
resource_type=<string>
limit=50
offset=0
```

**Response** `200`
```json
[
  {
    "id": "uuid",
    "organisation_id": "uuid",
    "actor_user_id": "uuid",
    "actor_email": "admin@example.com",
    "action": "task.status_changed",
    "resource_type": "task",
    "resource_id": "uuid",
    "metadata": {
      "from": "todo",
      "to": "in_progress",
      "task_title": "Design mockups"
    },
    "created_at": "2025-01-01T12:00:00Z"
  }
]
```

---

## Health

### GET /health

| Field | Value |
|---|---|
| **Hook** | Not used directly — called at app boot (optional) |
| **Purpose** | Ping backend before showing app UI |
| **Component** | `LoadingScreen` (only if needed) |

**Response** `200`
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0"
}
```

---

## TypeScript Types Reference

```typescript
// src/types/auth.ts
export interface User {
  id: string
  email: string
  full_name: string | null
  is_active: boolean
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: "bearer"
  expires_in: number
}

// src/types/org.ts
export interface Organization {
  id: string
  name: string
  slug: string
  description: string | null
  created_at: string
  updated_at: string
}

export interface Member {
  user_id: string
  email: string
  full_name: string | null
  role: OrgRole
  joined_at: string
}

export interface Invite {
  id: string
  token: string
  invitee_email: string
  role: OrgRole
  status: "pending" | "accepted" | "expired" | "revoked"
  expires_at: string
}

// src/types/project.ts
export interface Project {
  id: string
  organisation_id: string
  name: string
  description: string | null
  status: "active" | "archived"
  created_at: string
  updated_at: string
}

// src/types/task.ts
export type TaskStatus   = "todo" | "in_progress" | "done" | "blocked"
export type TaskPriority = "low" | "medium" | "high" | "urgent"

export interface Label {
  id: string
  name: string
  color: string
}

export interface Task {
  id: string
  project_id: string
  title: string
  description: string | null
  status: TaskStatus
  priority: TaskPriority
  position: number
  assignee_user_id: string | null
  created_by_user_id: string
  created_at: string
  updated_at: string
  deleted_at: string | null
  labels: Label[]
}

// src/types/comment.ts
export interface Comment {
  id: string
  task_id: string
  author_user_id: string
  author_email: string
  author_full_name: string | null
  body: string
  created_at: string
  updated_at: string
}

// src/types/audit.ts
export interface AuditLog {
  id: string
  organisation_id: string
  actor_user_id: string
  actor_email: string
  action: string
  resource_type: string
  resource_id: string
  metadata: Record<string, unknown>
  created_at: string
}

// Filter types
export interface TaskFilters {
  status?: TaskStatus
  priority?: TaskPriority
  assignee_user_id?: string
  label_id?: string
  limit?: number
  offset?: number
}

export interface AuditFilters {
  actor_user_id?: string
  action?: string
  resource_type?: string
  limit?: number
  offset?: number
}
```
