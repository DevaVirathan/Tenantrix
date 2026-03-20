import { useParams, Link } from "react-router-dom"
import { Building2, Users, Mail, FolderKanban, ArrowRight } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { useOrg } from "@/hooks/use-orgs"
import { useMembers } from "@/hooks/use-members"
import { useInvites } from "@/hooks/use-invites"
import { useProjects } from "@/hooks/use-projects"
import { RoleBadge } from "@/components/shared/role-badge"
import { ProjectStatusBadge } from "@/components/project/project-status-badge"
import { useAppStore } from "@/store/app-store"

function getGreeting() {
  const h = new Date().getHours()
  if (h < 12) return "Good morning"
  if (h < 17) return "Good afternoon"
  return "Good evening"
}

function getDayString() {
  return new Date().toLocaleDateString("en-US", {
    weekday: "long", month: "short", day: "numeric",
  })
}

export function OrgDashboardPage() {
  const { orgId } = useParams<{ orgId: string }>()
  const { data: org, isLoading: orgLoading } = useOrg(orgId!)
  const { data: members } = useMembers(orgId!)
  const { data: invites } = useInvites(orgId!)
  const { data: projects } = useProjects(orgId!)
  const user = useAppStore((s) => s.user)
  const activeMembership = useAppStore((s) => s.activeMembership)

  if (orgLoading) {
    return (
      <div className="space-y-6 max-w-4xl">
        <Skeleton className="h-12 w-72" />
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-28" />)}
        </div>
      </div>
    )
  }

  const pendingInvites = invites?.filter((i) => !i.expires_at || new Date(i.expires_at) > new Date()) ?? []
  const firstName = user?.full_name?.split(" ")[0] ?? user?.email ?? "there"

  return (
    <div className="max-w-4xl space-y-8">
      {/* Greeting */}
      <div className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight">{getGreeting()}, {firstName}</h1>
        <p className="text-muted-foreground text-sm">{getDayString()}</p>
      </div>

      {/* Org identity row */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 dark:bg-primary/15 dark:shadow-[0_0_12px_var(--neon-glow-spread)]">
            <Building2 className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h2 className="text-xl font-semibold">{org?.name}</h2>
            <p className="text-sm font-mono text-muted-foreground">/{org?.slug}</p>
          </div>
        </div>
        {activeMembership && <RoleBadge role={activeMembership.role} />}
      </div>

      {org?.description && (
        <p className="text-muted-foreground">{org.description}</p>
      )}

      {/* Stats grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Projects</CardTitle>
            <FolderKanban className="h-4 w-4 text-primary/60" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{projects?.length ?? "—"}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Members</CardTitle>
            <Users className="h-4 w-4 text-primary/60" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{members?.length ?? "—"}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Pending Invites</CardTitle>
            <Mail className="h-4 w-4 text-primary/60" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pendingInvites.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Created</CardTitle>
            <Building2 className="h-4 w-4 text-primary/60" />
          </CardHeader>
          <CardContent>
            <div className="text-sm font-medium">
              {org?.created_at ? new Date(org.created_at).toLocaleDateString() : "—"}
            </div>
          </CardContent>
        </Card>
      </div>

      <Separator className="dark:opacity-50" />

      {/* Recent projects */}
      {projects && projects.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">Projects</h3>
            <Button variant="ghost" size="sm" className="gap-1 text-xs" asChild>
              <Link to={`/orgs/${orgId}/projects`}>
                View all <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </Button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {projects.slice(0, 6).map((project) => (
              <Link
                key={project.id}
                to={`/orgs/${orgId}/projects/${project.id}/board`}
                className="flex items-center justify-between rounded-lg border bg-card px-4 py-3 transition-all duration-200 group hover:bg-accent/50 dark:hover:border-primary/20 dark:hover:shadow-[0_0_10px_var(--neon-glow-spread)]"
              >
                <div className="min-w-0">
                  <p className="font-medium text-sm truncate">{project.name}</p>
                  {project.description && (
                    <p className="text-xs text-muted-foreground truncate mt-0.5">{project.description}</p>
                  )}
                </div>
                <div className="flex items-center gap-2 shrink-0 ml-3">
                  <ProjectStatusBadge status={project.status} />
                  <ArrowRight className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
