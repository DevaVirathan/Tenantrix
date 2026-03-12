import { useState, useMemo } from "react"
import { useParams } from "react-router-dom"
import { ChevronLeft, ChevronRight, Plus } from "lucide-react"
import {
  startOfMonth, endOfMonth, startOfWeek, endOfWeek,
  addMonths, subMonths, eachDayOfInterval, format, isSameMonth, isToday,
} from "date-fns"
import { Button } from "@/components/ui/button"
import { IssueTypeIcon } from "@/components/task/issue-type-icon"
import { TaskDetailPanel } from "@/components/task/task-detail-panel"
import { CreateTaskDialog } from "@/components/task/create-task-dialog"
import { useProject } from "@/hooks/use-projects"
import { useTasks } from "@/hooks/use-tasks"
import { useAppStore } from "@/store/app-store"
import { cn } from "@/lib/utils"

export function CalendarViewPage() {
  const { orgId = "", projectId = "" } = useParams<{ orgId: string; projectId: string }>()
  const [currentMonth, setCurrentMonth] = useState(new Date())

  const { data: project } = useProject(orgId, projectId)
  const { data: tasks = [] } = useTasks(orgId, projectId)
  const openTaskPanel = useAppStore((s) => s.openTaskPanel)
  const membership = useAppStore((s) => s.activeMembership)
  const canCreate = membership?.role && ["member", "admin", "owner"].includes(membership.role)

  const monthStart = startOfMonth(currentMonth)
  const monthEnd = endOfMonth(currentMonth)
  const calendarStart = startOfWeek(monthStart)
  const calendarEnd = endOfWeek(monthEnd)
  const days = eachDayOfInterval({ start: calendarStart, end: calendarEnd })

  const tasksByDay = useMemo(() => {
    const map = new Map<string, typeof tasks>()
    for (const task of tasks) {
      if (!task.due_date) continue
      const key = format(new Date(task.due_date), "yyyy-MM-dd")
      const list = map.get(key) ?? []
      list.push(task)
      map.set(key, list)
    }
    return map
  }, [tasks])

  const weekDays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

  return (
    <div className="flex flex-col h-full gap-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h1 className="text-xl font-semibold">{project?.name ?? "Calendar"}</h1>
          <p className="text-sm text-muted-foreground">Tasks by due date</p>
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

      <div className="rounded-lg border bg-card overflow-hidden flex-1">
        {/* Week day headers */}
        <div className="grid grid-cols-7 border-b bg-muted/50">
          {weekDays.map((d) => (
            <div key={d} className="px-2 py-2 text-center text-xs font-medium text-muted-foreground">{d}</div>
          ))}
        </div>

        {/* Calendar grid */}
        <div className="grid grid-cols-7 auto-rows-fr" style={{ minHeight: 0 }}>
          {days.map((day) => {
            const key = format(day, "yyyy-MM-dd")
            const dayTasks = tasksByDay.get(key) ?? []
            const inMonth = isSameMonth(day, currentMonth)

            return (
              <div
                key={key}
                className={cn(
                  "border-b border-r p-1 min-h-24 flex flex-col",
                  !inMonth && "bg-muted/30",
                )}
              >
                <div className={cn(
                  "text-xs font-medium mb-1 w-6 h-6 flex items-center justify-center rounded-full",
                  isToday(day) && "bg-primary text-primary-foreground",
                  !inMonth && "text-muted-foreground/50",
                )}>
                  {format(day, "d")}
                </div>
                <div className="flex flex-col gap-0.5 overflow-hidden flex-1">
                  {dayTasks.slice(0, 3).map((task) => (
                    <button
                      key={task.id}
                      className="flex items-center gap-1 rounded px-1 py-0.5 text-xs hover:bg-accent truncate text-left"
                      onClick={() => openTaskPanel(task.id)}
                    >
                      <IssueTypeIcon type={task.issue_type} className="h-3 w-3 shrink-0" />
                      <span className="truncate">{task.title}</span>
                    </button>
                  ))}
                  {dayTasks.length > 3 && (
                    <span className="text-[10px] text-muted-foreground px-1">+{dayTasks.length - 3} more</span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      <TaskDetailPanel orgId={orgId} projectId={projectId} />
    </div>
  )
}
