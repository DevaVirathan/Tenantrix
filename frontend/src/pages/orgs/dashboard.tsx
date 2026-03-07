import { useParams } from "react-router-dom"
import { Building2, Users, Mail } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useOrg } from "@/hooks/use-orgs"
import { useMembers } from "@/hooks/use-members"
import { useInvites } from "@/hooks/use-invites"
import { RoleBadge } from "@/components/shared/role-badge"
import { useAppStore } from "@/store/app-store"

export function OrgDashboardPage() {
  const { orgId } = useParams<{ orgId: string }>()
  const { data: org, isLoading: orgLoading } = useOrg(orgId!)
  const { data: members } = useMembers(orgId!)
  const { data: invites } = useInvites(orgId!)
  const activeMembership = useAppStore((s) => s.activeMembership)

  if (orgLoading) {
    return (
      <div className="space-y-4 max-w-4xl">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-28" />)}
        </div>
      </div>
    )
  }

  const pendingInvites = invites?.filter((i) => !i.expires_at || new Date(i.expires_at) > new Date()) ?? []

  return (
    <div className="max-w-4xl space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
            <Building2 className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold">{org?.name}</h1>
            <p className="text-sm font-mono text-muted-foreground">/{org?.slug}</p>
          </div>
        </div>
        {activeMembership && <RoleBadge role={activeMembership.role} />}
      </div>

      {org?.description && (
        <p className="text-muted-foreground">{org.description}</p>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Members</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{members?.length ?? "—"}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Pending Invites</CardTitle>
            <Mail className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pendingInvites.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Created</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-sm font-medium">
              {org?.created_at ? new Date(org.created_at).toLocaleDateString() : "—"}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
