import { useState, useMemo } from "react"
import { useParams } from "react-router-dom"
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
import { Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { KanbanColumn } from "@/components/task/kanban-column"
import { TaskCard } from "@/components/task/task-card"
import { TaskDetailPanel } from "@/components/task/task-detail-panel"
import { TaskFiltersBar } from "@/components/task/task-filters"
import { CreateTaskDialog } from "@/components/task/create-task-dialog"
import { useProject } from "@/hooks/use-projects"
import { useTasks, useUpdateTask } from "@/hooks/use-tasks"
import { useProjectStates } from "@/hooks/use-project-states"
import { useAppStore } from "@/store/app-store"
import { useQueryClient } from "@tanstack/react-query"
import { queryKeys } from "@/lib/query-keys"
import type { Task, TaskFilters } from "@/types/task"

export function KanbanBoardPage() {
  const { orgId = "", projectId = "" } = useParams<{ orgId: string; projectId: string }>()
  const qc = useQueryClient()

  const [filters, setFilters] = useState<TaskFilters>({})
  const [activeTask, setActiveTask] = useState<Task | null>(null)

  const { data: project } = useProject(orgId, projectId)
  const { data: tasks = [], isLoading: tasksLoading } = useTasks(orgId, projectId, filters)
  const { data: states = [], isLoading: statesLoading } = useProjectStates(orgId, projectId)
  const { mutate: updateTask } = useUpdateTask(orgId, projectId)

  const membership = useAppStore((s) => s.activeMembership)
  const canCreate = membership?.role && ["member", "admin", "owner"].includes(membership.role)

  const isLoading = tasksLoading || statesLoading

  // Group tasks by state_id
  const tasksByState = useMemo(() => {
    const map: Record<string, Task[]> = {}
    for (const state of states) {
      map[state.id] = []
    }
    for (const task of tasks) {
      const stateId = task.state_id
      if (stateId && map[stateId]) {
        map[stateId].push(task)
      } else if (states.length > 0) {
        // Task has no state — put in first column
        map[states[0].id] = map[states[0].id] || []
        map[states[0].id].push(task)
      }
    }
    return map
  }, [tasks, states])

  // Build a set of state IDs for quick lookup
  const stateIdSet = useMemo(() => new Set(states.map((s) => s.id)), [states])

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

    // over.id is either a state id (column) or another task id
    const overIsColumn = stateIdSet.has(over.id as string)
    const newStateId: string = overIsColumn
      ? (over.id as string)
      : (tasks.find((t) => t.id === over.id)?.state_id ?? task.state_id ?? "")

    if (!newStateId) return

    if (newStateId === task.state_id) {
      // Reorder within the same column
      const col = tasksByState[task.state_id!] ?? []
      const oldIdx = col.findIndex((t) => t.id === taskId)
      const newIdx = col.findIndex((t) => t.id === over.id)
      if (oldIdx !== newIdx && newIdx !== -1) {
        const reordered = arrayMove(col, oldIdx, newIdx)
        const updated = tasks.map((t) => {
          const idx = reordered.findIndex((r) => r.id === t.id)
          return idx !== -1 ? { ...t, position: idx } : t
        })
        qc.setQueryData(queryKeys.tasks(orgId, projectId, filters as Record<string, unknown>), updated)
        updateTask({ taskId, data: { position: newIdx } })
      }
    } else {
      // Cross-column drag — update state_id
      const newCol = tasksByState[newStateId] ?? []
      const newPosition = newCol.length

      const targetState = states.find((s) => s.id === newStateId)
      const updated = tasks.map((t) =>
        t.id === taskId
          ? {
              ...t,
              state_id: newStateId,
              state: targetState
                ? { id: targetState.id, name: targetState.name, color: targetState.color, group: targetState.group }
                : t.state,
              position: newPosition,
            }
          : t
      )
      qc.setQueryData(queryKeys.tasks(orgId, projectId, filters as Record<string, unknown>), updated)
      updateTask({ taskId, data: { state_id: newStateId, position: newPosition } })
    }
  }

  return (
    <div className="flex flex-col h-full gap-4">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h1 className="text-xl font-semibold">{project?.name ?? "Board"}</h1>
          {project?.description && (
            <p className="text-sm text-muted-foreground">{project.description}</p>
          )}
        </div>
        <div className="flex items-center gap-2">
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
      <TaskFiltersBar orgId={orgId} projectId={projectId} filters={filters} onChange={setFilters} />

      {/* Kanban Board */}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragOver={handleDragOver}
        onDragEnd={handleDragEnd}
      >
        <div className="flex gap-4 overflow-x-auto pb-4 flex-1 items-start">
          {states.map((state) => (
            <KanbanColumn
              key={state.id}
              state={state}
              tasks={tasksByState[state.id] ?? []}
              orgId={orgId}
              projectId={projectId}
              projectIdentifier={project?.identifier}
              isLoading={isLoading}
            />
          ))}
        </div>

        <DragOverlay>
          {activeTask && <TaskCard task={activeTask} orgId={orgId} projectIdentifier={project?.identifier} />}
        </DragOverlay>
      </DndContext>

      {/* Task detail slide-over */}
      <TaskDetailPanel orgId={orgId} projectId={projectId} />
    </div>
  )
}
