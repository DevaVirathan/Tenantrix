import { format } from "date-fns"
import {
  ChevronDown, ChevronRight, Play, Square, Trash2, MoreHorizontal,
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Progress } from "@/components/ui/progress"
import { IssueTypeIcon } from "@/components/task/issue-type-icon"
import { useAppStore } from "@/store/app-store"
import { useUpdateSprint, useDeleteSprint } from "@/hooks/use-sprints"
import type { Sprint } from "@/types/sprint"
import type { Task } from "@/types/task"
import { TASK_STATUS_LABELS } from "@/types/task"
import { cn } from "@/lib/utils"

interface Props {
  sprint: Sprint
  tasks: Task[]
  orgId: string
  projectId: string
  expanded: boolean
  onToggle: () => void
  onMoveTask?: (taskId: string, sprintId: string | null) => void
}

const statusColor: Record<string, string> = {
  backlog: "bg-muted text-muted-foreground",
  active: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  closed: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
}

export function SprintCard({ sprint, tasks, orgId, projectId, expanded, onToggle, onMoveTask }: Props) {
  const openTaskPanel = useAppStore((s) => s.openTaskPanel)
  const { mutate: updateSprint } = useUpdateSprint(orgId, projectId)
  const { mutate: deleteSprint } = useDeleteSprint(orgId, projectId)

  const progress = sprint.task_count > 0
    ? Math.round((sprint.done_count / sprint.task_count) * 100)
    : 0

  const dateRange = sprint.start_date && sprint.end_date
    ? `${format(new Date(sprint.start_date), "MMM d")} — ${format(new Date(sprint.end_date), "MMM d, yyyy")}`
    : sprint.start_date
    ? `Starts ${format(new Date(sprint.start_date), "MMM d, yyyy")}`
    : null

  function handleStart() {
    updateSprint({ sprintId: sprint.id, data: { status: "active" } })
  }
  function handleClose() {
    updateSprint({ sprintId: sprint.id, data: { status: "closed" } })
  }
  function handleDelete() {
    deleteSprint(sprint.id)
  }

  return (
    <div className="rounded-lg border bg-card">
      {/* Header */}
      <div
        className="flex items-center gap-2 px-4 py-3 cursor-pointer select-none"
        onClick={onToggle}
      >
        {expanded
          ? <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />
          : <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
        }
        <h3 className="font-medium text-sm flex-1 truncate">{sprint.name}</h3>
        <Badge variant="outline" className={cn("text-xs", statusColor[sprint.status])}>
          {sprint.status}
        </Badge>
        {dateRange && (
          <span className="text-xs text-muted-foreground hidden sm:inline">{dateRange}</span>
        )}
        <span className="text-xs text-muted-foreground">
          {sprint.task_count} task{sprint.task_count !== 1 ? "s" : ""}
          {sprint.total_points > 0 && ` · ${sprint.total_points} pts`}
        </span>

        <DropdownMenu>
          <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
            <Button variant="ghost" size="icon" className="h-7 w-7">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {sprint.status === "backlog" && (
              <DropdownMenuItem onClick={handleStart}>
                <Play className="h-4 w-4 mr-2" /> Start Sprint
              </DropdownMenuItem>
            )}
            {sprint.status === "active" && (
              <DropdownMenuItem onClick={handleClose}>
                <Square className="h-4 w-4 mr-2" /> Close Sprint
              </DropdownMenuItem>
            )}
            {sprint.status === "backlog" && sprint.task_count === 0 && (
              <DropdownMenuItem onClick={handleDelete} className="text-destructive">
                <Trash2 className="h-4 w-4 mr-2" /> Delete
              </DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Progress bar */}
      {sprint.task_count > 0 && (
        <div className="px-4 pb-2">
          <Progress value={progress} className="h-1.5" />
        </div>
      )}

      {/* Tasks list */}
      {expanded && (
        <div className="border-t divide-y">
          {tasks.length === 0 && (
            <p className="px-4 py-6 text-sm text-muted-foreground text-center">
              No tasks in this sprint. Drag tasks here or assign them from the backlog.
            </p>
          )}
          {tasks.map((task) => (
            <div
              key={task.id}
              className="flex items-center gap-3 px-4 py-2 hover:bg-accent/50 cursor-pointer text-sm"
              onClick={() => openTaskPanel(task.id)}
            >
              <IssueTypeIcon type={task.issue_type} className="h-4 w-4 shrink-0" />
              <span className="flex-1 truncate">{task.title}</span>
              <Badge variant="outline" className="text-xs">
                {TASK_STATUS_LABELS[task.status]}
              </Badge>
              {task.story_points != null && (
                <span className="text-xs text-muted-foreground">{task.story_points} pts</span>
              )}
              {onMoveTask && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 text-xs"
                  onClick={(e) => { e.stopPropagation(); onMoveTask(task.id, null) }}
                >
                  Remove
                </Button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
