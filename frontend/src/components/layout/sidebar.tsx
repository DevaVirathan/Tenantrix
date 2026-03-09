import { NavLink, useParams } from "react-router-dom"
import { LayoutDashboard, Users, Mail, Settings, ClipboardList, Activity } from "lucide-react"
import { OrgSwitcher } from "./org-switcher"
import { useAppStore } from "@/store/app-store"
import { hasRole } from "@/lib/rbac"
import { cn } from "@/lib/utils"
import { ScrollArea } from "@/components/ui/scroll-area"

interface NavItem {
  label: string
  to: string
  icon: React.ComponentType<{ className?: string }>
  adminOnly?: boolean
}

export function Sidebar() {
  const { orgId } = useParams<{ orgId: string }>()
  const activeMembership = useAppStore((s) => s.activeMembership)
  const role = activeMembership?.role ?? null

  const navItems: NavItem[] = [
    { label: "Dashboard", to: `/orgs/${orgId}`, icon: LayoutDashboard },
    { label: "Members", to: `/orgs/${orgId}/members`, icon: Users },
    { label: "Invites", to: `/orgs/${orgId}/invites`, icon: Mail },
    { label: "Projects", to: `/orgs/${orgId}/projects`, icon: ClipboardList },
    { label: "Settings", to: `/orgs/${orgId}/settings`, icon: Settings, adminOnly: true },
    { label: "Audit Logs", to: `/orgs/${orgId}/audit-logs`, icon: Activity, adminOnly: true },
  ]

  const visibleItems = navItems.filter(
    (item) => !item.adminOnly || hasRole(role, "admin")
  )

  return (
    <aside className="flex h-full w-56 shrink-0 flex-col border-r bg-sidebar">
      {/* Org switcher */}
      <div className="border-b px-3 py-3">
        <OrgSwitcher />
      </div>

      {/* Nav */}
      <ScrollArea className="flex-1 px-2 py-3">
        <nav className="flex flex-col gap-0.5">
          {visibleItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === `/orgs/${orgId}`}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-accent text-accent-foreground"
                    : "text-muted-foreground hover:bg-accent/50 hover:text-foreground"
                )
              }
            >
              <item.icon className="h-4 w-4 shrink-0" />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </ScrollArea>
    </aside>
  )
}
