import { useState, useMemo } from "react"
import { useParams, useNavigate } from "react-router-dom"
import {
  DndContext,
  closestCorners,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core"
import type { DragEndEvent, DragOverEvent, DragStartEvent } from "@dnd-kit/core"
import { arrayMove } from "@dnd-kit/sortable"
import { ArrowLeft, Plus, Settings } from "lucide-react"
import { Button } from "@/components/ui/button"
import { KanbanColumn } from "@/components/task/kanban-column"
import { TaskCard } from "@/components/task/task-card"
import { TaskDetailPanel } from "@/components/task/task-detail-panel"
import { TaskFiltersBar } from "@/components/task/task-filters"
import { CreateTaskDialog } from "@/components/task/create-task-dialog"
import { useProject } from "@/hooks/use-projects"
import { useTasks, useUpdateTask } from "@/hooks/use-tasks"
import { useAppStore } from "@/store/app-store"
import { useQueryClient } from "@tanstack/react-query"
import { queryKeys } from "@/lib/query-keys"
import type { Task, TaskStatus, TaskFilters } from "@/types/task"
import { KANBAN_COLUMNS } from "@/types/task"

export function KanbanBoardPage() {
  const { orgId = "", projectId = "" } = useParams<{ orgId: string; projectId: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()

  const [filters, setFilters] = useState<TaskFilters>({})
  const [activeTask, setActiveTask] = useState<Task | null>(null)

  const { data: project } = useProject(orgId, projectId)
  const { data: tasks = [], isLoading } = useTasks(orgId, projectId, filters)
  const { mutate: updateTask } = useUpdateTask(orgId, projectId)

  const membership = useAppStore((s) => s.activeMembership)
  const canCreate = membership?.role && ["member", "admin", "owner"].includes(membership.role)

  // Group tasks by status
  const tasksByStatus = useMemo(() => {
    const map: Record<TaskStatus, Task[]> = {
      todo: [], in_progress: [], done: [], blocked: [],
    }
    for (const task of tasks) map[task.status].push(task)
    return map
  }, [tasks])

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } })
  )

  function handleDragStart(event: DragStartEvent) {
    const task = tasks.find((t) => t.id === event.active.id)
    setActiveTask(task ?? null)
  }

  function handleDragOver(_event: DragOverEvent) {
    // Handled in dragEnd for cross-column drops
  }

  function handleDragEnd(event: DragEndEvent) {
    setActiveTask(null)
    const { active, over } = event
    if (!over) return

    const taskId = active.id as string
    const task = tasks.find((t) => t.id === taskId)
    if (!task) return

    // over.id is either a column status or another task id
    const overIsColumn = KANBAN_COLUMNS.includes(over.id as TaskStatus)
    const newStatus: TaskStatus = overIsColumn
      ? (over.id as TaskStatus)
      : (tasks.find((t) => t.id === over.id)?.status ?? task.status)

    if (newStatus === task.status) {
      // Reorder within the same column
      const col = tasksByStatus[task.status]
      const oldIdx = col.findIndex((t) => t.id === taskId)
      const newIdx = col.findIndex((t) => t.id === over.id)
      if (oldIdx !== newIdx && newIdx !== -1) {
        const reordered = arrayMove(col, oldIdx, newIdx)
        // Optimistic update
        const updated = tasks.map((t) => {
          const idx = reordered.findIndex((r) => r.id === t.id)
          return idx !== -1 ? { ...t, position: idx } : t
        })
        qc.setQueryData(queryKeys.tasks(orgId, projectId), updated)
        updateTask({ taskId, data: { position: newIdx } })
      }
    } else {
      // Cross-column drag
      const newCol = tasksByStatus[newStatus]
      const newPosition = newCol.length

      // Optimistic update
      const updated = tasks.map((t) =>
        t.id === taskId ? { ...t, status: newStatus, position: newPosition } : t
      )
      qc.setQueryData(queryKeys.tasks(orgId, projectId), updated)
      updateTask({ taskId, data: { status: newStatus, position: newPosition } })
    }
  }

  return (
    <div className="flex flex-col h-full gap-4">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" onClick={() => navigate(`/orgs/${orgId}/projects`)}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-xl font-semibold">{project?.name ?? "Board"}</h1>
            {project?.description && (
              <p className="text-sm text-muted-foreground">{project.description}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(`/orgs/${orgId}/projects/${projectId}`)}
          >
            <Settings className="h-4 w-4 mr-1" />
            Settings
          </Button>
          {canCreate && (
            <CreateTaskDialog orgId={orgId} projectId={projectId}>
              <Button size="sm">
                <Plus className="h-4 w-4 mr-1" />
                New task
              </Button>
            </CreateTaskDialog>
          )}
        </div>
      </div>

      {/* Filters */}
      <TaskFiltersBar orgId={orgId} filters={filters} onChange={setFilters} />

      {/* Kanban Board */}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragOver={handleDragOver}
        onDragEnd={handleDragEnd}
      >
        <div className="flex gap-4 overflow-x-auto pb-4 flex-1 items-start">
          {KANBAN_COLUMNS.map((status) => (
            <KanbanColumn
              key={status}
              status={status}
              tasks={tasksByStatus[status]}
              orgId={orgId}
              projectId={projectId}
              isLoading={isLoading}
            />
          ))}
        </div>

        <DragOverlay>
          {activeTask && <TaskCard task={activeTask} orgId={orgId} />}
        </DragOverlay>
      </DndContext>

      {/* Task detail slide-over */}
      <TaskDetailPanel orgId={orgId} projectId={projectId} />
    </div>
  )
}
