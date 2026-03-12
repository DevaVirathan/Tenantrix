import { useState } from "react"
import { NavLink, useParams, useLocation } from "react-router-dom"
import {
  LayoutDashboard, Users, Mail, Settings, Activity,
  FolderKanban, ChevronDown, ChevronRight, LayoutGrid, ListTodo,
  List, Calendar, GanttChart, BarChart3, Menu,
} from "lucide-react"
import { OrgSwitcher } from "./org-switcher"
import { useAppStore } from "@/store/app-store"
import { useProjects } from "@/hooks/use-projects"
import { hasRole } from "@/lib/rbac"
import { cn } from "@/lib/utils"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"

interface NavItem {
  label: string
  to: string
  icon: React.ComponentType<{ className?: string }>
  adminOnly?: boolean
}

// ── Shared nav content ────────────────────────────────────────────────────────

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const { orgId } = useParams<{ orgId: string }>()
  const location = useLocation()
  const activeMembership = useAppStore((s) => s.activeMembership)
  const role = activeMembership?.role ?? null

  const { data: projects = [] } = useProjects(orgId ?? "")

  const [expandedProjects, setExpandedProjects] = useState<Set<string>>(new Set())
  const activeProjectId = useParams<{ projectId?: string }>().projectId

  function toggleProject(projectId: string) {
    setExpandedProjects((prev) => {
      const next = new Set(prev)
      if (next.has(projectId)) next.delete(projectId)
      else next.add(projectId)
      return next
    })
  }

  function isProjectExpanded(projectId: string) {
    return expandedProjects.has(projectId) || activeProjectId === projectId
  }

  const topNavItems: NavItem[] = [
    { label: "Dashboard", to: `/orgs/${orgId}`, icon: LayoutDashboard },
    { label: "Members", to: `/orgs/${orgId}/members`, icon: Users },
    { label: "Invites", to: `/orgs/${orgId}/invites`, icon: Mail },
    { label: "Settings", to: `/orgs/${orgId}/settings`, icon: Settings, adminOnly: true },
    { label: "Audit Logs", to: `/orgs/${orgId}/audit-logs`, icon: Activity, adminOnly: true },
  ]

  const visibleTopItems = topNavItems.filter(
    (item) => !item.adminOnly || hasRole(role, "admin")
  )

  const canCreateProject = hasRole(role, "member")
  const isProjectsActive = location.pathname.includes("/projects")

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    cn(
      "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors",
      isActive
        ? "bg-accent text-accent-foreground"
        : "text-muted-foreground hover:bg-accent/50 hover:text-foreground"
    )

  const subNavClass = ({ isActive }: { isActive: boolean }) =>
    cn(
      "flex items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors",
      isActive
        ? "bg-accent text-accent-foreground font-medium"
        : "text-muted-foreground hover:bg-accent/50 hover:text-foreground"
    )

  const projectViews: { to: string; icon: React.ComponentType<{ className?: string }>; label: string }[] = [
    { to: "board", icon: LayoutDashboard, label: "Board" },
    { to: "backlog", icon: ListTodo, label: "Backlog" },
    { to: "list", icon: List, label: "List" },
    { to: "calendar", icon: Calendar, label: "Calendar" },
    { to: "timeline", icon: GanttChart, label: "Timeline" },
    { to: "modules", icon: FolderKanban, label: "Modules" },
    { to: "analytics", icon: BarChart3, label: "Analytics" },
  ]

  return (
    <>
      <div className="border-b px-3 py-3">
        <OrgSwitcher />
      </div>

      <ScrollArea className="flex-1 px-2 py-3">
        <nav className="flex flex-col gap-0.5">
          {visibleTopItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === `/orgs/${orgId}`}
              className={navLinkClass}
              onClick={onNavigate}
            >
              <item.icon className="h-4 w-4 shrink-0" />
              {item.label}
            </NavLink>
          ))}

          {/* Projects section */}
          <div className="mt-2">
            <div className="flex items-center justify-between px-3 py-1.5">
              <NavLink
                to={`/orgs/${orgId}/projects`}
                className={cn(
                  "flex items-center gap-2 text-xs font-semibold uppercase tracking-wider transition-colors",
                  isProjectsActive && !activeProjectId
                    ? "text-foreground"
                    : "text-muted-foreground hover:text-foreground"
                )}
                onClick={onNavigate}
              >
                <LayoutGrid className="h-3.5 w-3.5" />
                Projects
              </NavLink>
            </div>

            <div className="flex flex-col gap-0.5">
              {projects.map((project) => {
                const expanded = isProjectExpanded(project.id)
                const isActive = activeProjectId === project.id

                return (
                  <div key={project.id}>
                    <button
                      onClick={() => toggleProject(project.id)}
                      className={cn(
                        "w-full flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors text-left",
                        isActive
                          ? "bg-accent text-accent-foreground"
                          : "text-muted-foreground hover:bg-accent/50 hover:text-foreground"
                      )}
                    >
                      <FolderKanban className="h-4 w-4 shrink-0" />
                      <span className="flex-1 truncate">{project.name}</span>
                      {expanded
                        ? <ChevronDown className="h-3.5 w-3.5 shrink-0 opacity-60" />
                        : <ChevronRight className="h-3.5 w-3.5 shrink-0 opacity-60" />
                      }
                    </button>

                    {expanded && (
                      <div className="ml-4 flex flex-col gap-0.5 border-l pl-2.5 mt-0.5 mb-1">
                        {projectViews.map((view) => (
                          <NavLink
                            key={view.to}
                            to={`/orgs/${orgId}/projects/${project.id}/${view.to}`}
                            className={subNavClass}
                            onClick={onNavigate}
                          >
                            <view.icon className="h-3.5 w-3.5 shrink-0" />
                            {view.label}
                          </NavLink>
                        ))}
                        {hasRole(role, "admin") && (
                          <NavLink
                            to={`/orgs/${orgId}/projects/${project.id}`}
                            end
                            className={subNavClass}
                            onClick={onNavigate}
                          >
                            <Settings className="h-3.5 w-3.5 shrink-0" />
                            Settings
                          </NavLink>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}

              {canCreateProject && projects.length === 0 && (
                <NavLink
                  to={`/orgs/${orgId}/projects`}
                  className="flex items-center gap-2 rounded-md px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground"
                  onClick={onNavigate}
                >
                  + New project
                </NavLink>
              )}
            </div>
          </div>
        </nav>
      </ScrollArea>
    </>
  )
}

// ── Desktop sidebar ───────────────────────────────────────────────────────────

export function Sidebar() {
  return (
    <aside
      className="hidden md:flex h-full w-56 shrink-0 flex-col border-r bg-sidebar"
      role="navigation"
      aria-label="Main navigation"
    >
      <SidebarContent />
    </aside>
  )
}

// ── Mobile sidebar (hamburger sheet) ──────────────────────────────────────────

export function MobileSidebar() {
  const [open, setOpen] = useState(false)

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="md:hidden h-8 w-8" aria-label="Open menu">
          <Menu className="h-5 w-5" />
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-64 p-0">
        <div className="flex h-full flex-col">
          <SidebarContent onNavigate={() => setOpen(false)} />
        </div>
      </SheetContent>
    </Sheet>
  )
}
