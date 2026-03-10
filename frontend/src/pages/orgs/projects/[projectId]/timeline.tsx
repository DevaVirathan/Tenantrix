import { useMemo, useState } from "react"
import { useParams } from "react-router-dom"
import { ChevronLeft, ChevronRight, Plus } from "lucide-react"
import {
  startOfMonth, endOfMonth, eachDayOfInterval, format,
  addMonths, subMonths, differenceInDays, isWithinInterval, isToday,
} from "date-fns"
import { Button } from "@/components/ui/button"
import { IssueTypeIcon } from "@/components/task/issue-type-icon"
import { TaskDetailPanel } from "@/components/task/task-detail-panel"
import { CreateTaskDialog } from "@/components/task/create-task-dialog"
import { useProject } from "@/hooks/use-projects"
import { useTasks } from "@/hooks/use-tasks"
import { useMembers } from "@/hooks/use-members"
import { useAppStore } from "@/store/app-store"
import { cn } from "@/lib/utils"

const STATUS_COLORS: Record<string, string> = {
  todo: "bg-gray-400",
  in_progress: "bg-blue-500",
  done: "bg-emerald-500",
  blocked: "bg-red-500",
}

export function TimelineViewPage() {
  const { orgId = "", projectId = "" } = useParams<{ orgId: string; projectId: string }>()
  const [currentMonth, setCurrentMonth] = useState(new Date())

  const { data: project } = useProject(orgId, projectId)
  const { data: tasks = [] } = useTasks(orgId, projectId)
  const { data: members = [] } = useMembers(orgId)
  const openTaskPanel = useAppStore((s) => s.openTaskPanel)
  const membership = useAppStore((s) => s.activeMembership)
  const canCreate = membership?.role && ["member", "admin", "owner"].includes(membership.role)

  const rangeStart = startOfMonth(currentMonth)
  const rangeEnd = endOfMonth(currentMonth)
  const days = eachDayOfInterval({ start: rangeStart, end: rangeEnd })
  const totalDays = days.length

  // Filter tasks that have at least a start or due date in range
  const timelineTasks = useMemo(() => {
    return tasks.filter((t) => {
      if (!t.start_date && !t.due_date) return false
      const start = t.start_date ? new Date(t.start_date) : null
      const end = t.due_date ? new Date(t.due_date) : null
      if (start && isWithinInterval(start, { start: rangeStart, end: rangeEnd })) return true
      if (end && isWithinInterval(end, { start: rangeStart, end: rangeEnd })) return true
      if (start && end && start <= rangeStart && end >= rangeEnd) return true
      return false
    })
  }, [tasks, rangeStart, rangeEnd])

  function getBarStyle(startDate: string | null, dueDate: string | null) {
    const s = startDate ? new Date(startDate) : rangeStart
    const e = dueDate ? new Date(dueDate) : rangeEnd
    const clampedStart = s < rangeStart ? rangeStart : s
    const clampedEnd = e > rangeEnd ? rangeEnd : e
    const left = (differenceInDays(clampedStart, rangeStart) / totalDays) * 100
    const width = ((differenceInDays(clampedEnd, clampedStart) + 1) / totalDays) * 100
    return { left: `${Math.max(0, left)}%`, width: `${Math.min(100 - left, width)}%` }
  }

  function getMemberName(userId: string | null) {
    if (!userId) return "Unassigned"
    const m = members.find((m) => m.user_id === userId)
    return m?.full_name ?? m?.email ?? "Unknown"
  }

  return (
    <div className="flex flex-col h-full gap-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h1 className="text-xl font-semibold">{project?.name ?? "Timeline"}</h1>
          <p className="text-sm text-muted-foreground">Gantt-style timeline view</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => setCurrentMonth(subMonths(currentMonth, 1))}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="text-sm font-medium w-32 text-center">{format(currentMonth, "MMMM yyyy")}</span>
          <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}>
            <ChevronRight className="h-4 w-4" />
          </Button>
          {canCreate && (
            <CreateTaskDialog orgId={orgId} projectId={projectId}>
              <Button size="sm"><Plus className="h-4 w-4 mr-1" /> New task</Button>
            </CreateTaskDialog>
          )}
        </div>
      </div>

      <div className="rounded-lg border bg-card overflow-auto flex-1">
        {/* Day headers */}
        <div className="flex border-b bg-muted/50 sticky top-0 z-10">
          <div className="w-48 shrink-0 px-3 py-2 text-xs font-medium text-muted-foreground border-r">Task</div>
          <div className="flex-1 flex">
            {days.map((day) => (
              <div
                key={day.toISOString()}
                className={cn(
                  "flex-1 min-w-[28px] text-center text-[10px] py-2 border-r text-muted-foreground",
                  isToday(day) && "bg-primary/10 font-semibold text-primary",
                )}
              >
                {format(day, "d")}
              </div>
            ))}
          </div>
        </div>

        {/* Task rows */}
        {timelineTasks.length === 0 && (
          <div className="py-12 text-center text-sm text-muted-foreground">
            No tasks with dates in {format(currentMonth, "MMMM yyyy")}.
          </div>
        )}
        {timelineTasks.map((task) => {
          const barStyle = getBarStyle(task.start_date, task.due_date)
          return (
            <div key={task.id} className="flex border-b hover:bg-accent/30 transition-colors">
              <div
                className="w-48 shrink-0 px-3 py-2 flex items-center gap-2 border-r cursor-pointer truncate"
                onClick={() => openTaskPanel(task.id)}
              >
                <IssueTypeIcon type={task.issue_type} className="h-3.5 w-3.5 shrink-0" />
                <span className="text-xs truncate">{task.title}</span>
              </div>
              <div className="flex-1 relative h-8 my-auto">
                <div
                  className={cn(
                    "absolute top-1 h-6 rounded-full cursor-pointer flex items-center px-2 text-[10px] text-white font-medium truncate",
                    STATUS_COLORS[task.status] ?? "bg-gray-400",
                  )}
                  style={barStyle}
                  onClick={() => openTaskPanel(task.id)}
                  title={`${task.title} — ${getMemberName(task.assignee_user_id)}`}
                >
                  {task.title}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      <TaskDetailPanel orgId={orgId} projectId={projectId} />
    </div>
  )
}
