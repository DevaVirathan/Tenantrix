import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable"
import { useDroppable } from "@dnd-kit/core"
import { Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { TaskCard } from "./task-card"
import { CreateTaskDialog } from "./create-task-dialog"
import type { Task } from "@/types/task"
import type { ProjectState } from "@/types/project-state"
import { cn } from "@/lib/utils"

interface KanbanColumnProps {
  state: ProjectState
  tasks: Task[]
  orgId: string
  projectId: string
  projectIdentifier?: string | null
  isLoading?: boolean
}

export function KanbanColumn({ state, tasks, orgId, projectId, projectIdentifier, isLoading }: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({ id: state.id })
  const taskIds = tasks.map((t) => t.id)

  return (
    <div className="flex flex-col min-w-65 flex-1">
      {/* Column header */}
      <div
        className="rounded-t-lg border-t-2 bg-muted/40 px-3 py-2 flex items-center justify-between"
        style={{ borderTopColor: state.color }}
      >
        <div className="flex items-center gap-2">
          <span
            className="inline-block h-2.5 w-2.5 rounded-full shrink-0"
            style={{ backgroundColor: state.color }}
          />
          <span className="text-sm font-semibold">{state.name}</span>
          <span className="rounded-full bg-muted px-1.5 py-0.5 text-xs text-muted-foreground font-medium">
            {tasks.length}
          </span>
        </div>
        <CreateTaskDialog orgId={orgId} projectId={projectId} defaultStateId={state.id}>
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
              <TaskCard key={task.id} task={task} orgId={orgId} projectIdentifier={projectIdentifier} />
            ))}
          </SortableContext>
        )}

        {!isLoading && tasks.length === 0 && (
          <CreateTaskDialog orgId={orgId} projectId={projectId} defaultStateId={state.id}>
            <button className="w-full rounded border border-dashed border-border py-2 text-xs text-muted-foreground hover:border-primary/40 hover:text-foreground transition-colors">
              + Add task
            </button>
          </CreateTaskDialog>
        )}
      </div>
    </div>
  )
}
