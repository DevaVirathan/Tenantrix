import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable"
import { useDroppable } from "@dnd-kit/core"
import { Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { TaskCard } from "./task-card"
import { CreateTaskDialog } from "./create-task-dialog"
import type { Task, TaskStatus } from "@/types/task"
import { TASK_STATUS_LABELS } from "@/types/task"
import { cn } from "@/lib/utils"

const COLUMN_STYLES: Record<TaskStatus, string> = {
  todo:        "border-t-slate-400",
  in_progress: "border-t-blue-400",
  done:        "border-t-green-400",
  blocked:     "border-t-red-400",
}

interface KanbanColumnProps {
  status: TaskStatus
  tasks: Task[]
  orgId: string
  projectId: string
  isLoading?: boolean
}

export function KanbanColumn({ status, tasks, orgId, projectId, isLoading }: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({ id: status })
  const taskIds = tasks.map((t) => t.id)

  return (
    <div className="flex flex-col min-w-65 flex-1">
      {/* Column header */}
      <div className={cn("rounded-t-lg border-t-2 bg-muted/40 px-3 py-2 flex items-center justify-between", COLUMN_STYLES[status])}>
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold">{TASK_STATUS_LABELS[status]}</span>
          <span className="rounded-full bg-muted px-1.5 py-0.5 text-xs text-muted-foreground font-medium">
            {tasks.length}
          </span>
        </div>
        <CreateTaskDialog orgId={orgId} projectId={projectId} defaultStatus={status}>
          <Button variant="ghost" size="icon" className="h-6 w-6">
            <Plus className="h-3.5 w-3.5" />
          </Button>
        </CreateTaskDialog>
      </div>

      {/* Drop zone */}
      <div
        ref={setNodeRef}
        className={cn(
          "flex-1 rounded-b-lg border border-t-0 p-2 space-y-2 min-h-50 transition-colors",
          isOver ? "bg-primary/5 border-primary/30" : "bg-muted/20 border-border"
        )}
      >
        {isLoading ? (
          <>
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-16 w-full" />
          </>
        ) : (
          <SortableContext items={taskIds} strategy={verticalListSortingStrategy}>
            {tasks.map((task) => (
              <TaskCard key={task.id} task={task} orgId={orgId} />
            ))}
          </SortableContext>
        )}

        {/* Add task button at bottom (only when no tasks) */}
        {!isLoading && tasks.length === 0 && (
          <CreateTaskDialog orgId={orgId} projectId={projectId} defaultStatus={status}>
            <button className="w-full rounded border border-dashed border-border py-2 text-xs text-muted-foreground hover:border-primary/40 hover:text-foreground transition-colors">
              + Add task
            </button>
          </CreateTaskDialog>
        )}
      </div>
    </div>
  )
}
