import { Moon, Sun, ChevronRight } from "lucide-react"
import { Link, useParams, useMatches } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { NotificationBell } from "@/components/layout/notification-bell"
import { UserMenu } from "@/components/layout/user-menu"
import { useTheme } from "@/providers/theme-provider"
import { useAppStore } from "@/store/app-store"
import { useProject } from "@/hooks/use-projects"

function Breadcrumbs() {
  const { orgId, projectId } = useParams<{ orgId?: string; projectId?: string }>()
  const activeOrg = useAppStore((s) => s.activeOrg)
  const { data: project } = useProject(orgId ?? "", projectId ?? "")
  const matches = useMatches()
  const lastMatch = matches[matches.length - 1]
  const pathname = lastMatch?.pathname ?? ""

  // Build breadcrumb segments
  const crumbs: { label: string; to?: string }[] = []

  if (orgId && activeOrg) {
    crumbs.push({ label: activeOrg.name, to: `/orgs/${orgId}` })
  }

  if (projectId && project) {
    crumbs.push({ label: "Projects", to: `/orgs/${orgId}/projects` })
    crumbs.push({ label: project.name, to: `/orgs/${orgId}/projects/${projectId}/board` })
  } else if (pathname.includes("/projects")) {
    crumbs.push({ label: "Projects" })
  } else if (pathname.includes("/members")) {
    crumbs.push({ label: "Members" })
  } else if (pathname.includes("/invites")) {
    crumbs.push({ label: "Invites" })
  } else if (pathname.includes("/settings")) {
    crumbs.push({ label: "Settings" })
  } else if (pathname.includes("/audit-logs")) {
    crumbs.push({ label: "Audit Logs" })
  }

  if (pathname.endsWith("/board") && projectId) {
    crumbs.push({ label: "Board" })
  }

  if (crumbs.length === 0) return null

  return (
    <nav className="flex items-center gap-1 text-sm min-w-0">
      {crumbs.map((crumb, idx) => {
        const isLast = idx === crumbs.length - 1
        return (
          <span key={idx} className="flex items-center gap-1 min-w-0">
            {idx > 0 && <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/60 shrink-0" />}
            {crumb.to && !isLast ? (
              <Link
                to={crumb.to}
                className="text-muted-foreground hover:text-foreground transition-colors truncate max-w-32"
              >
                {crumb.label}
              </Link>
            ) : (
              <span className={isLast ? "font-medium text-foreground truncate max-w-48" : "text-muted-foreground truncate max-w-32"}>
                {crumb.label}
              </span>
            )}
          </span>
        )
      })}
    </nav>
  )
}

export function TopBar() {
  const { theme, toggleTheme } = useTheme()

  return (
    <header className="h-12 border-b border-border bg-background/95 backdrop-blur-sm flex items-center px-4 gap-3 sticky top-0 z-40">
      {/* App name */}
      <Link to="/orgs" className="font-semibold text-sm text-foreground shrink-0">
        Tenantrix
      </Link>

      {/* Breadcrumb */}
      <div className="flex-1 min-w-0">
        <Breadcrumbs />
      </div>

      {/* Actions */}
      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8 shrink-0"
        onClick={toggleTheme}
        aria-label="Toggle theme"
      >
        {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
      </Button>

      <NotificationBell />
      <UserMenu />
    </header>
  )
}
