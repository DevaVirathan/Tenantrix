import { lazy, Suspense } from "react"
import { createBrowserRouter, Navigate } from "react-router-dom"
import { AuthLayout } from "@/layouts/auth-layout"
import { DashboardLayout } from "@/layouts/dashboard-layout"

// Lazy-loaded pages for code-splitting
const LoginPage = lazy(() => import("@/pages/auth/login").then((m) => ({ default: m.LoginPage })))
const RegisterPage = lazy(() => import("@/pages/auth/register").then((m) => ({ default: m.RegisterPage })))
const AcceptInvitePage = lazy(() => import("@/pages/auth/accept-invite").then((m) => ({ default: m.AcceptInvitePage })))
const OrgsPage = lazy(() => import("@/pages/orgs/index").then((m) => ({ default: m.OrgsPage })))
const OrgDashboardPage = lazy(() => import("@/pages/orgs/dashboard").then((m) => ({ default: m.OrgDashboardPage })))
const MembersPage = lazy(() => import("@/pages/orgs/members").then((m) => ({ default: m.MembersPage })))
const InvitesPage = lazy(() => import("@/pages/orgs/invites").then((m) => ({ default: m.InvitesPage })))
const OrgSettingsPage = lazy(() => import("@/pages/orgs/settings").then((m) => ({ default: m.OrgSettingsPage })))
const ProjectsPage = lazy(() => import("@/pages/orgs/projects/index").then((m) => ({ default: m.ProjectsPage })))
const ProjectSettingsPage = lazy(() => import("@/pages/orgs/projects/[projectId]/settings").then((m) => ({ default: m.ProjectSettingsPage })))
const KanbanBoardPage = lazy(() => import("@/pages/orgs/projects/[projectId]/board").then((m) => ({ default: m.KanbanBoardPage })))
const BacklogPage = lazy(() => import("@/pages/orgs/projects/[projectId]/backlog").then((m) => ({ default: m.BacklogPage })))
const ListViewPage = lazy(() => import("@/pages/orgs/projects/[projectId]/list").then((m) => ({ default: m.ListViewPage })))
const CalendarViewPage = lazy(() => import("@/pages/orgs/projects/[projectId]/calendar").then((m) => ({ default: m.CalendarViewPage })))
const TimelineViewPage = lazy(() => import("@/pages/orgs/projects/[projectId]/timeline").then((m) => ({ default: m.TimelineViewPage })))
const AnalyticsPage = lazy(() => import("@/pages/orgs/projects/[projectId]/analytics").then((m) => ({ default: m.AnalyticsPage })))
const ModulesPage = lazy(() => import("@/pages/orgs/projects/[projectId]/modules").then((m) => ({ default: m.ModulesPage })))
const AuditLogsPage = lazy(() => import("@/pages/orgs/audit-logs").then((m) => ({ default: m.AuditLogsPage })))

function LazyPage({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<div className="flex items-center justify-center h-40 text-muted-foreground">Loading…</div>}>{children}</Suspense>
}

function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-4">
      <h1 className="text-4xl font-bold">404</h1>
      <p className="text-muted-foreground">Page not found.</p>
      <a href="/orgs" className="text-primary hover:underline">
        Go home
      </a>
    </div>
  )
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Navigate to="/orgs" replace />,
  },
  {
    element: <AuthLayout />,
    children: [
      { path: "/login", element: <LazyPage><LoginPage /></LazyPage> },
      { path: "/register", element: <LazyPage><RegisterPage /></LazyPage> },
    ],
  },
  {
    path: "/invite/:token",
    element: <LazyPage><AcceptInvitePage /></LazyPage>,
  },
  {
    element: <DashboardLayout />,
    children: [
      { path: "/orgs", element: <LazyPage><OrgsPage /></LazyPage> },
      { path: "/orgs/new", element: <LazyPage><OrgsPage /></LazyPage> },
      { path: "/orgs/:orgId", element: <LazyPage><OrgDashboardPage /></LazyPage> },
      { path: "/orgs/:orgId/members", element: <LazyPage><MembersPage /></LazyPage> },
      { path: "/orgs/:orgId/invites", element: <LazyPage><InvitesPage /></LazyPage> },
      { path: "/orgs/:orgId/settings", element: <LazyPage><OrgSettingsPage /></LazyPage> },
      { path: "/orgs/:orgId/projects", element: <LazyPage><ProjectsPage /></LazyPage> },
      { path: "/orgs/:orgId/projects/:projectId", element: <LazyPage><ProjectSettingsPage /></LazyPage> },
      { path: "/orgs/:orgId/projects/:projectId/board", element: <LazyPage><KanbanBoardPage /></LazyPage> },
      { path: "/orgs/:orgId/projects/:projectId/backlog", element: <LazyPage><BacklogPage /></LazyPage> },
      { path: "/orgs/:orgId/projects/:projectId/list", element: <LazyPage><ListViewPage /></LazyPage> },
      { path: "/orgs/:orgId/projects/:projectId/calendar", element: <LazyPage><CalendarViewPage /></LazyPage> },
      { path: "/orgs/:orgId/projects/:projectId/timeline", element: <LazyPage><TimelineViewPage /></LazyPage> },
      { path: "/orgs/:orgId/projects/:projectId/modules", element: <LazyPage><ModulesPage /></LazyPage> },
      { path: "/orgs/:orgId/projects/:projectId/analytics", element: <LazyPage><AnalyticsPage /></LazyPage> },
      { path: "/orgs/:orgId/audit-logs", element: <LazyPage><AuditLogsPage /></LazyPage> },
    ],
  },
  {
    path: "*",
    element: <NotFoundPage />,
  },
])
