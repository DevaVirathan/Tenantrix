import { useParams } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { apiClient } from "@/lib/api-client"
import { useProject } from "@/hooks/use-projects"
import { TASK_STATUS_LABELS, TASK_PRIORITY_LABELS } from "@/types/task"
import type { TaskStatus, TaskPriority } from "@/types/task"
import { useMembers } from "@/hooks/use-members"
import { cn } from "@/lib/utils"

interface AnalyticsData {
  total_tasks: number
  total_points: number
  done_points: number
  by_status: Record<string, number>
  by_priority: Record<string, number>
  by_assignee: Record<string, number>
}

const STATUS_COLORS: Record<string, string> = {
  todo: "bg-gray-400",
  in_progress: "bg-blue-500",
  done: "bg-emerald-500",
  blocked: "bg-red-500",
}

const PRIORITY_COLORS: Record<string, string> = {
  low: "bg-gray-400",
  medium: "bg-yellow-500",
  high: "bg-orange-500",
  urgent: "bg-red-500",
}

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="rounded-lg border bg-card p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
      {sub && <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>}
    </div>
  )
}

function BarChart({ data, labels, colors }: { data: Record<string, number>; labels: Record<string, string>; colors: Record<string, string> }) {
  const total = Object.values(data).reduce((s, v) => s + v, 0) || 1
  return (
    <div className="space-y-2">
      {Object.entries(labels).map(([key, label]) => {
        const count = data[key] ?? 0
        const pct = Math.round((count / total) * 100)
        return (
          <div key={key} className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground w-24 shrink-0">{label}</span>
            <div className="flex-1 bg-muted rounded-full h-5 overflow-hidden">
              <div
                className={cn("h-full rounded-full transition-all", colors[key] ?? "bg-gray-400")}
                style={{ width: `${pct}%` }}
              />
            </div>
            <span className="text-xs font-medium w-10 text-right">{count}</span>
          </div>
        )
      })}
    </div>
  )
}

export function AnalyticsPage() {
  const { orgId = "", projectId = "" } = useParams<{ orgId: string; projectId: string }>()
  const { data: project } = useProject(orgId, projectId)
  const { data: members = [] } = useMembers(orgId)

  const { data, isLoading } = useQuery({
    queryKey: ["org", orgId, "project", projectId, "analytics"],
    queryFn: () =>
      apiClient.get(`organizations/${orgId}/projects/${projectId}/analytics`).json<AnalyticsData>(),
    enabled: !!orgId && !!projectId,
    staleTime: 1000 * 60,
  })

  function getMemberName(userId: string) {
    if (userId === "unassigned") return "Unassigned"
    const m = members.find((m) => m.user_id === userId)
    return m?.full_name ?? m?.email ?? "Unknown"
  }

  if (isLoading || !data) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Loading analytics…</p>
      </div>
    )
  }

  const completionPct = data.total_tasks > 0
    ? Math.round(((data.by_status?.done ?? 0) / data.total_tasks) * 100)
    : 0

  return (
    <div className="flex flex-col h-full gap-6 overflow-auto">
      <div>
        <h1 className="text-xl font-semibold">{project?.name ?? "Analytics"}</h1>
        <p className="text-sm text-muted-foreground">Project insights and metrics</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Tasks" value={data.total_tasks} />
        <StatCard label="Completion" value={`${completionPct}%`} sub={`${data.by_status?.done ?? 0} of ${data.total_tasks} done`} />
        <StatCard label="Total Points" value={data.total_points} />
        <StatCard label="Done Points" value={data.done_points} />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="rounded-lg border bg-card p-4">
          <h3 className="text-sm font-semibold mb-4">By Status</h3>
          <BarChart data={data.by_status} labels={TASK_STATUS_LABELS} colors={STATUS_COLORS} />
        </div>
        <div className="rounded-lg border bg-card p-4">
          <h3 className="text-sm font-semibold mb-4">By Priority</h3>
          <BarChart data={data.by_priority} labels={TASK_PRIORITY_LABELS} colors={PRIORITY_COLORS} />
        </div>
      </div>

      {/* By Assignee */}
      <div className="rounded-lg border bg-card p-4">
        <h3 className="text-sm font-semibold mb-4">By Assignee</h3>
        <div className="space-y-2">
          {Object.entries(data.by_assignee).map(([userId, count]) => {
            const total = data.total_tasks || 1
            const pct = Math.round((count / total) * 100)
            return (
              <div key={userId} className="flex items-center gap-3">
                <span className="text-xs text-muted-foreground w-32 shrink-0 truncate">{getMemberName(userId)}</span>
                <div className="flex-1 bg-muted rounded-full h-5 overflow-hidden">
                  <div className="h-full rounded-full bg-primary/60 transition-all" style={{ width: `${pct}%` }} />
                </div>
                <span className="text-xs font-medium w-10 text-right">{count}</span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
