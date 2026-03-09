import { useState } from "react"
import { useParams, Navigate } from "react-router-dom"
import { Activity, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Separator } from "@/components/ui/separator"
import { AuditFiltersBar } from "@/components/audit/audit-filters"
import { AuditTimeline } from "@/components/audit/audit-timeline"
import { useAuditLogs } from "@/hooks/use-audit-logs"
import { useMembers } from "@/hooks/use-members"
import { useAppStore } from "@/store/app-store"
import { hasRole } from "@/lib/rbac"
import type { AuditFilters } from "@/types/audit"

type PageFilters = Omit<AuditFilters, "limit" | "offset">

export function AuditLogsPage() {
  const { orgId } = useParams<{ orgId: string }>()
  const activeMembership = useAppStore((s) => s.activeMembership)
  const role = activeMembership?.role ?? null

  const [filters, setFilters] = useState<PageFilters>({})

  // Guard — non-admins get redirected away
  if (!hasRole(role, "admin")) {
    return <Navigate to={`/orgs/${orgId}`} replace />
  }

  const {
    data,
    isLoading,
    isFetchingNextPage,
    hasNextPage,
    fetchNextPage,
    refetch,
  } = useAuditLogs(orgId!, filters)

  const { data: members = [] } = useMembers(orgId!)

  // Build actorId → display name map for the timeline
  const actorNames: Record<string, string> = {}
  for (const m of members) {
    actorNames[m.user_id] = m.full_name ?? m.email ?? m.user_id
  }

  const allLogs = data?.pages.flat() ?? []

  return (
    <div className="flex flex-col gap-6 max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-muted-foreground" />
          <div>
            <h1 className="text-xl font-semibold">Audit Logs</h1>
            <p className="text-sm text-muted-foreground">
              All organisation activity — newest first
            </p>
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="gap-2"
          onClick={() => refetch()}
          disabled={isLoading}
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <AuditFiltersBar filters={filters} onChange={setFilters} />

      <Separator />

      {/* Timeline / skeletons / empty state */}
      {isLoading ? (
        <div className="space-y-5">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="flex gap-3">
              <Skeleton className="h-7 w-7 rounded-full shrink-0" />
              <div className="flex-1 space-y-1.5 pt-1">
                <Skeleton className="h-4 w-2/3" />
                <Skeleton className="h-3.5 w-1/3" />
              </div>
            </div>
          ))}
        </div>
      ) : allLogs.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-16 text-center">
          <Activity className="h-10 w-10 text-muted-foreground/30" />
          <p className="text-muted-foreground">
            No audit events match your filters.
          </p>
        </div>
      ) : (
        <>
          <AuditTimeline logs={allLogs} actorNames={actorNames} />

          {hasNextPage && (
            <Button
              variant="outline"
              size="sm"
              className="self-center"
              onClick={() => fetchNextPage()}
              disabled={isFetchingNextPage}
            >
              {isFetchingNextPage ? "Loading…" : "Load more"}
            </Button>
          )}
        </>
      )}
    </div>
  )
}
