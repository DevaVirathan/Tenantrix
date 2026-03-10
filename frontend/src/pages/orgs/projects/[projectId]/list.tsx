import { useState } from "react"
import { useParams } from "react-router-dom"
import { Plus, ArrowUpDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { TaskDetailPanel } from "@/components/task/task-detail-panel"
import { TaskFiltersBar } from "@/components/task/task-filters"
import { CreateTaskDialog } from "@/components/task/create-task-dialog"
import { IssueTypeIcon } from "@/components/task/issue-type-icon"
import { useProject } from "@/hooks/use-projects"
import { useTasks } from "@/hooks/use-tasks"
import { useAppStore } from "@/store/app-store"
import { useMembers } from "@/hooks/use-members"
import type { Task, TaskFilters, TaskStatus, TaskPriority } from "@/types/task"
import { TASK_STATUS_LABELS, TASK_PRIORITY_LABELS } from "@/types/task"
import { cn } from "@/lib/utils"

type SortKey = "title" | "status" | "priority" | "assignee" | "due_date" | "story_points"

const priorityOrder: Record<TaskPriority, number> = { low: 0, medium: 1, high: 2, urgent: 3 }
const statusOrder: Record<TaskStatus, number> = { todo: 0, in_progress: 1, done: 2, blocked: 3 }

export function ListViewPage() {
  const { orgId = "", projectId = "" } = useParams<{ orgId: string; projectId: string }>()
  const [filters, setFilters] = useState<TaskFilters>({})
  const [sortKey, setSortKey] = useState<SortKey>("status")
  const [sortAsc, setSortAsc] = useState(true)

  const { data: project } = useProject(orgId, projectId)
  const { data: tasks = [], isLoading } = useTasks(orgId, projectId, filters)
  const { data: members = [] } = useMembers(orgId)
  const openTaskPanel = useAppStore((s) => s.openTaskPanel)
  const membership = useAppStore((s) => s.activeMembership)
  const canCreate = membership?.role && ["member", "admin", "owner"].includes(membership.role)

  function getMemberName(userId: string | null) {
    if (!userId) return "Unassigned"
    const m = members.find((m) => m.user_id === userId)
    return m?.full_name ?? m?.email ?? "Unknown"
  }

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortAsc(!sortAsc)
    else { setSortKey(key); setSortAsc(true) }
  }

  const sorted = [...tasks].sort((a, b) => {
    let cmp = 0
    switch (sortKey) {
      case "title": cmp = a.title.localeCompare(b.title); break
      case "status": cmp = statusOrder[a.status] - statusOrder[b.status]; break
      case "priority": cmp = priorityOrder[a.priority] - priorityOrder[b.priority]; break
      case "assignee": cmp = getMemberName(a.assignee_user_id).localeCompare(getMemberName(b.assignee_user_id)); break
      case "due_date": cmp = (a.due_date ?? "").localeCompare(b.due_date ?? ""); break
      case "story_points": cmp = (a.story_points ?? 0) - (b.story_points ?? 0); break
    }
    return sortAsc ? cmp : -cmp
  })

  function SortHeader({ label, field }: { label: string; field: SortKey }) {
    return (
      <button
        className="flex items-center gap-1 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
        onClick={() => toggleSort(field)}
      >
        {label}
        <ArrowUpDown className={cn("h-3 w-3", sortKey === field && "text-foreground")} />
      </button>
    )
  }

  return (
    <div className="flex flex-col h-full gap-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h1 className="text-xl font-semibold">{project?.name ?? "List"}</h1>
          <p className="text-sm text-muted-foreground">Table view of all tasks</p>
        </div>
        {canCreate && (
          <CreateTaskDialog orgId={orgId} projectId={projectId}>
            <Button size="sm"><Plus className="h-4 w-4 mr-1" /> New task</Button>
          </CreateTaskDialog>
        )}
      </div>

      <TaskFiltersBar orgId={orgId} filters={filters} onChange={setFilters} />

      <div className="rounded-lg border bg-card overflow-auto flex-1">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr className="border-b">
              <th className="text-left px-4 py-2 w-8"></th>
              <th className="text-left px-4 py-2 min-w-[200px]"><SortHeader label="Title" field="title" /></th>
              <th className="text-left px-4 py-2 w-28"><SortHeader label="Status" field="status" /></th>
              <th className="text-left px-4 py-2 w-24"><SortHeader label="Priority" field="priority" /></th>
              <th className="text-left px-4 py-2 w-36"><SortHeader label="Assignee" field="assignee" /></th>
              <th className="text-left px-4 py-2 w-28"><SortHeader label="Due date" field="due_date" /></th>
              <th className="text-right px-4 py-2 w-16"><SortHeader label="Pts" field="story_points" /></th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr><td colSpan={7} className="text-center py-8 text-muted-foreground">Loading…</td></tr>
            )}
            {!isLoading && sorted.length === 0 && (
              <tr><td colSpan={7} className="text-center py-8 text-muted-foreground">No tasks found.</td></tr>
            )}
            {sorted.map((task) => (
              <tr
                key={task.id}
                className="border-b hover:bg-accent/50 cursor-pointer transition-colors"
                onClick={() => openTaskPanel(task.id)}
              >
                <td className="px-4 py-2"><IssueTypeIcon type={task.issue_type} className="h-4 w-4" /></td>
                <td className="px-4 py-2 font-medium truncate max-w-xs">{task.title}</td>
                <td className="px-4 py-2">
                  <Badge variant="outline" className="text-xs">{TASK_STATUS_LABELS[task.status]}</Badge>
                </td>
                <td className="px-4 py-2">
                  <Badge variant="outline" className="text-xs">{TASK_PRIORITY_LABELS[task.priority]}</Badge>
                </td>
                <td className="px-4 py-2 text-xs text-muted-foreground truncate">{getMemberName(task.assignee_user_id)}</td>
                <td className="px-4 py-2 text-xs text-muted-foreground">
                  {task.due_date ? new Date(task.due_date).toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "—"}
                </td>
                <td className="px-4 py-2 text-right text-xs text-muted-foreground">{task.story_points ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <TaskDetailPanel orgId={orgId} projectId={projectId} />
    </div>
  )
}
