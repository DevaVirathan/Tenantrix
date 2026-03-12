import { useParams } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { isAfter, parseISO, startOfToday } from "date-fns"
import { apiClient } from "@/lib/api-client"
import { useProject } from "@/hooks/use-projects"
import { TASK_PRIORITY_LABELS } from "@/types/task"
import { useMembers } from "@/hooks/use-members"
import { useTasks } from "@/hooks/use-tasks"
import { cn } from "@/lib/utils"

interface StateCount {
  id: string
  name: string
  color: string
  count: number
}

interface SprintSummary {
  id: string
  name: string
  status: string
  start_date: string | null
  end_date: string | null
  total_tasks: number
  done_tasks: number
  total_points: number
  done_points: number
}

interface AnalyticsData {
  total_tasks: number
  total_points: number
  done_points: number
  by_status: Record<string, number>
  by_state: StateCount[]
  by_priority: Record<string, number>
  by_assignee: Record<string, number>
  sprints: SprintSummary[]
}

const PRIORITY_COLORS: Record<string, string> = {
  low: "bg-gray-400",
  medium: "bg-yellow-500",
  high: "bg-orange-500",
  urgent: "bg-red-500",
}

function StatCard({ label, value, sub, accent }: { label: string; value: string | number; sub?: string; accent?: string }) {
  return (
    <div className="rounded-lg border bg-card p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className={cn("text-2xl font-bold mt-1", accent)}>{value}</p>
      {sub && <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>}
    </div>
  )
}

function StateBarChart({ states }: { states: StateCount[] }) {
  const total = states.reduce((s, v) => s + v.count, 0) || 1
  if (states.length === 0) {
    return <p className="text-sm text-muted-foreground text-center py-4">No states configured.</p>
  }
  return (
    <div className="space-y-2">
      {states.map((s) => {
        const pct = Math.round((s.count / total) * 100)
        return (
          <div key={s.id} className="flex items-center gap-3">
            <span className="flex items-center gap-1.5 text-xs text-muted-foreground w-28 shrink-0 truncate">
              <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: s.color }} />
              {s.name}
            </span>
            <div className="flex-1 bg-muted rounded-full h-5 overflow-hidden">
              <div
                className="h-full rounded-full transition-all"
                style={{ width: `${pct}%`, backgroundColor: s.color }}
              />
            </div>
            <span className="text-xs font-medium w-10 text-right">{s.count}</span>
          </div>
        )
      })}
    </div>
  )
}

function PriorityBarChart({ data }: { data: Record<string, number> }) {
  const total = Object.values(data).reduce((s, v) => s + v, 0) || 1
  return (
    <div className="space-y-2">
      {Object.entries(TASK_PRIORITY_LABELS).map(([key, label]) => {
        const count = data[key] ?? 0
        const pct = Math.round((count / total) * 100)
        return (
          <div key={key} className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground w-24 shrink-0">{label}</span>
            <div className="flex-1 bg-muted rounded-full h-5 overflow-hidden">
              <div
                className={cn("h-full rounded-full transition-all", PRIORITY_COLORS[key] ?? "bg-gray-400")}
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
  const { data: allTasks = [] } = useTasks(orgId, projectId)

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

  const overdueCount = allTasks.filter((t) => {
    if (!t.due_date) return false
    const isOverdue = isAfter(startOfToday(), parseISO(t.due_date.slice(0, 10)))
    const isDone = t.state?.group === "completed" || t.state?.group === "cancelled"
    return isOverdue && !isDone
  }).length

  const unassignedCount = allTasks.filter((t) => !t.assignee_user_id).length

  if (isLoading || !data) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Loading analytics…</p>
      </div>
    )
  }

  const byState = data.by_state ?? []
  const completedCount = byState
    .filter((s) => s.name.toLowerCase().includes("done") || s.name.toLowerCase().includes("complete"))
    .reduce((sum, s) => sum + s.count, 0)
  const completionPct = data.total_tasks > 0
    ? Math.round((completedCount / data.total_tasks) * 100)
    : 0

  return (
    <div className="flex flex-col h-full gap-6 overflow-auto pb-6">
      <div>
        <h1 className="text-xl font-semibold">{project?.name ?? "Analytics"}</h1>
        <p className="text-sm text-muted-foreground">Project insights and metrics</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Tasks" value={data.total_tasks} />
        <StatCard
          label="Completion"
          value={`${completionPct}%`}
          sub={`${completedCount} of ${data.total_tasks} done`}
        />
        <StatCard label="Story Points" value={data.total_points} sub={`${data.done_points} pts done`} />
        <StatCard
          label="Overdue"
          value={overdueCount}
          sub="past due date"
          accent={overdueCount > 0 ? "text-destructive" : undefined}
        />
      </div>

      {/* State & Priority charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="rounded-lg border bg-card p-4">
          <h3 className="text-sm font-semibold mb-4">By State</h3>
          <StateBarChart states={byState} />
        </div>
        <div className="rounded-lg border bg-card p-4">
          <h3 className="text-sm font-semibold mb-4">By Priority</h3>
          <PriorityBarChart data={data.by_priority} />
        </div>
      </div>

      {/* By Assignee */}
      <div className="rounded-lg border bg-card p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold">By Assignee</h3>
          {unassignedCount > 0 && (
            <span className="text-xs text-muted-foreground">{unassignedCount} unassigned</span>
          )}
        </div>
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

      {/* Sprint Velocity */}
      {data.sprints.length > 0 && (
        <div className="rounded-lg border bg-card p-4">
          <h3 className="text-sm font-semibold mb-4">Sprint Velocity</h3>
          <div className="space-y-3">
            {data.sprints.map((sprint) => {
              const taskPct = sprint.total_tasks > 0 ? Math.round((sprint.done_tasks / sprint.total_tasks) * 100) : 0
              const pointPct = sprint.total_points > 0 ? Math.round((sprint.done_points / sprint.total_points) * 100) : 0
              return (
                <div key={sprint.id} className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium truncate max-w-[200px]">{sprint.name}</span>
                    <span className={cn(
                      "text-[10px] px-1.5 py-0.5 rounded-full",
                      sprint.status === "active" ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
                        : sprint.status === "closed" ? "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400"
                        : "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
                    )}>{sprint.status}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-muted-foreground w-12 shrink-0">Tasks</span>
                    <div className="flex-1 bg-muted rounded-full h-4 overflow-hidden">
                      <div className="h-full rounded-full bg-primary/70 transition-all" style={{ width: `${taskPct}%` }} />
                    </div>
                    <span className="text-[10px] w-16 text-right">{sprint.done_tasks}/{sprint.total_tasks}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-muted-foreground w-12 shrink-0">Points</span>
                    <div className="flex-1 bg-muted rounded-full h-4 overflow-hidden">
                      <div className="h-full rounded-full bg-emerald-500/70 transition-all" style={{ width: `${pointPct}%` }} />
                    </div>
                    <span className="text-[10px] w-16 text-right">{sprint.done_points}/{sprint.total_points}</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
