import { useState, useCallback } from "react"
import { useParams } from "react-router-dom"
import { Plus, ArrowUpDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select"
import { TaskDetailPanel } from "@/components/task/task-detail-panel"
import { TaskFiltersBar } from "@/components/task/task-filters"
import { CreateTaskDialog } from "@/components/task/create-task-dialog"
import { IssueTypeIcon } from "@/components/task/issue-type-icon"
import { PriorityIcon } from "@/components/task/priority-icon"
import { useProject } from "@/hooks/use-projects"
import { useTasks, useUpdateTask, useBulkUpdateTasks } from "@/hooks/use-tasks"
import { useProjectStates } from "@/hooks/use-project-states"
import { useAppStore } from "@/store/app-store"
import { useMembers } from "@/hooks/use-members"
import type { TaskFilters, TaskPriority } from "@/types/task"
import { TASK_PRIORITY_LABELS } from "@/types/task"
import { cn } from "@/lib/utils"

type SortKey = "title" | "status" | "priority" | "assignee" | "due_date" | "story_points"

const priorityOrder: Record<TaskPriority, number> = { low: 0, medium: 1, high: 2, urgent: 3 }

export function ListViewPage() {
  const { orgId = "", projectId = "" } = useParams<{ orgId: string; projectId: string }>()
  const [filters, setFilters] = useState<TaskFilters>({})
  const [sortKey, setSortKey] = useState<SortKey>("status")
  const [sortAsc, setSortAsc] = useState(true)
  const [selected, setSelected] = useState<Set<string>>(new Set())

  const { data: project } = useProject(orgId, projectId)
  const { data: tasks = [], isLoading } = useTasks(orgId, projectId, filters)
  const { data: members = [] } = useMembers(orgId)
  const { data: states = [] } = useProjectStates(orgId, projectId)
  const { mutate: updateTask } = useUpdateTask(orgId, projectId)
  const bulkUpdate = useBulkUpdateTasks(orgId, projectId)
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

  const toggleSelect = useCallback((id: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  const toggleAll = useCallback(() => {
    if (selected.size === tasks.length) setSelected(new Set())
    else setSelected(new Set(tasks.map((t) => t.id)))
  }, [selected.size, tasks])

  function handleBulkAction(updates: Record<string, unknown>) {
    if (selected.size === 0) return
    bulkUpdate.mutate(
      { task_ids: Array.from(selected), updates },
      { onSuccess: () => setSelected(new Set()) },
    )
  }

  const sorted = [...tasks].sort((a, b) => {
    let cmp = 0
    switch (sortKey) {
      case "title": cmp = a.title.localeCompare(b.title); break
      case "status": cmp = (a.state?.name ?? a.status).localeCompare(b.state?.name ?? b.status); break
      case "priority": cmp = priorityOrder[a.priority] - priorityOrder[b.priority]; break
      case "assignee": cmp = getMemberName(a.assignee_user_id).localeCompare(getMemberName(b.assignee_user_id)); break
      case "due_date": cmp = (a.due_date ?? "").localeCompare(b.due_date ?? ""); break
      case "story_points": cmp = (a.story_points ?? 0) - (b.story_points ?? 0); break
    }
    return sortAsc ? cmp : -cmp
  })

  const priorities = Object.keys(TASK_PRIORITY_LABELS) as TaskPriority[]

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

      <TaskFiltersBar orgId={orgId} projectId={projectId} filters={filters} onChange={setFilters} />

      {/* Bulk actions bar */}
      {selected.size > 0 && (
        <div className="flex items-center gap-3 rounded-lg border bg-accent/50 px-4 py-2 text-sm">
          <span className="font-medium">{selected.size} selected</span>
          <Select onValueChange={(v) => handleBulkAction({ state_id: v })}>
            <SelectTrigger className="h-7 w-32 text-xs">
              <SelectValue placeholder="Set state" />
            </SelectTrigger>
            <SelectContent>
              {states.map((s) => (
                <SelectItem key={s.id} value={s.id}>
                  <span className="flex items-center gap-2">
                    <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: s.color }} />
                    {s.name}
                  </span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select onValueChange={(v) => handleBulkAction({ priority: v })}>
            <SelectTrigger className="h-7 w-28 text-xs">
              <SelectValue placeholder="Priority" />
            </SelectTrigger>
            <SelectContent>
              {priorities.map((p) => (
                <SelectItem key={p} value={p}>
                  <span className="flex items-center gap-2">
                    <PriorityIcon priority={p} />
                    {TASK_PRIORITY_LABELS[p]}
                  </span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select onValueChange={(v) => handleBulkAction({ assignee_user_id: v === "__none__" ? null : v })}>
            <SelectTrigger className="h-7 w-32 text-xs">
              <SelectValue placeholder="Assignee" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__none__">Unassigned</SelectItem>
              {members.map((m) => (
                <SelectItem key={m.user_id} value={m.user_id}>{m.full_name ?? m.email}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="ghost" size="sm" className="ml-auto text-xs" onClick={() => setSelected(new Set())}>
            Clear
          </Button>
        </div>
      )}

      <div className="rounded-lg border bg-card overflow-auto flex-1">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr className="border-b">
              <th className="text-left px-3 py-2 w-8">
                <Checkbox
                  checked={tasks.length > 0 && selected.size === tasks.length}
                  onCheckedChange={toggleAll}
                  aria-label="Select all"
                />
              </th>
              <th className="text-left px-3 py-2 w-8"></th>
              <th className="text-left px-3 py-2 min-w-[200px]"><SortHeader label="Title" field="title" /></th>
              <th className="text-left px-3 py-2 w-32"><SortHeader label="Status" field="status" /></th>
              <th className="text-left px-3 py-2 w-28"><SortHeader label="Priority" field="priority" /></th>
              <th className="text-left px-3 py-2 w-36"><SortHeader label="Assignee" field="assignee" /></th>
              <th className="text-left px-3 py-2 w-28"><SortHeader label="Due date" field="due_date" /></th>
              <th className="text-right px-3 py-2 w-16"><SortHeader label="Pts" field="story_points" /></th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr><td colSpan={8} className="text-center py-8 text-muted-foreground">Loading…</td></tr>
            )}
            {!isLoading && sorted.length === 0 && (
              <tr><td colSpan={8} className="text-center py-8 text-muted-foreground">No tasks found.</td></tr>
            )}
            {sorted.map((task) => (
              <tr
                key={task.id}
                className={cn(
                  "border-b hover:bg-accent/50 transition-colors",
                  selected.has(task.id) && "bg-accent/30",
                )}
              >
                <td className="px-3 py-2" onClick={(e) => e.stopPropagation()}>
                  <Checkbox
                    checked={selected.has(task.id)}
                    onCheckedChange={() => toggleSelect(task.id)}
                    aria-label={`Select ${task.title}`}
                  />
                </td>
                <td className="px-3 py-2 cursor-pointer" onClick={() => openTaskPanel(task.id)}>
                  <IssueTypeIcon type={task.issue_type} className="h-4 w-4" />
                </td>
                <td className="px-3 py-2 font-medium truncate max-w-xs cursor-pointer" onClick={() => openTaskPanel(task.id)}>
                  {task.title}
                </td>
                {/* Inline editable state */}
                <td className="px-3 py-2" onClick={(e) => e.stopPropagation()}>
                  <Select
                    value={task.state_id ?? ""}
                    onValueChange={(v) => updateTask({ taskId: task.id, data: { state_id: v } })}
                  >
                    <SelectTrigger className="h-7 text-xs border-0 bg-transparent shadow-none px-1 hover:bg-accent focus:ring-0 w-full justify-start gap-1.5">
                      {task.state && (
                        <span className="inline-block h-2 w-2 rounded-full shrink-0" style={{ backgroundColor: task.state.color }} />
                      )}
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {states.map((s) => (
                        <SelectItem key={s.id} value={s.id}>
                          <span className="flex items-center gap-2">
                            <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: s.color }} />
                            {s.name}
                          </span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </td>
                {/* Inline editable priority */}
                <td className="px-3 py-2" onClick={(e) => e.stopPropagation()}>
                  <Select
                    value={task.priority}
                    onValueChange={(v) => updateTask({ taskId: task.id, data: { priority: v as TaskPriority } })}
                  >
                    <SelectTrigger className="h-7 text-xs border-0 bg-transparent shadow-none px-1 hover:bg-accent focus:ring-0 w-full justify-start gap-1.5">
                      <PriorityIcon priority={task.priority} />
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {priorities.map((p) => (
                        <SelectItem key={p} value={p}>
                          <span className="flex items-center gap-2">
                            <PriorityIcon priority={p} />
                            {TASK_PRIORITY_LABELS[p]}
                          </span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </td>
                {/* Inline editable assignee */}
                <td className="px-3 py-2" onClick={(e) => e.stopPropagation()}>
                  <Select
                    value={task.assignee_user_id ?? "__none__"}
                    onValueChange={(v) => updateTask({ taskId: task.id, data: { assignee_user_id: v === "__none__" ? null : v } })}
                  >
                    <SelectTrigger className="h-7 text-xs border-0 bg-transparent shadow-none px-1 hover:bg-accent focus:ring-0 w-full justify-start">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__none__">Unassigned</SelectItem>
                      {members.map((m) => (
                        <SelectItem key={m.user_id} value={m.user_id}>{m.full_name ?? m.email}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </td>
                <td className="px-3 py-2 text-xs text-muted-foreground cursor-pointer" onClick={() => openTaskPanel(task.id)}>
                  {task.due_date ? new Date(task.due_date).toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "—"}
                </td>
                <td className="px-3 py-2 text-right text-xs text-muted-foreground cursor-pointer" onClick={() => openTaskPanel(task.id)}>
                  {task.story_points ?? "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <TaskDetailPanel orgId={orgId} projectId={projectId} />
    </div>
  )
}
