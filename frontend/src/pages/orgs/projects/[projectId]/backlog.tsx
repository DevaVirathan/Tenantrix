import { useCallback, useMemo, useState } from "react"
import { useParams } from "react-router-dom"
import { Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select"
import { SprintCard } from "@/components/sprint/sprint-card"
import { CreateSprintDialog } from "@/components/sprint/create-sprint-dialog"
import { CreateTaskDialog } from "@/components/task/create-task-dialog"
import { TaskDetailPanel } from "@/components/task/task-detail-panel"
import { IssueTypeIcon } from "@/components/task/issue-type-icon"
import { Badge } from "@/components/ui/badge"
import { useProject } from "@/hooks/use-projects"
import { useTasks, useUpdateTask } from "@/hooks/use-tasks"
import { useSprints } from "@/hooks/use-sprints"
import { useAppStore } from "@/store/app-store"
import type { Task } from "@/types/task"
import { TASK_STATUS_LABELS } from "@/types/task"
import { cn } from "@/lib/utils"

function StateChip({ task }: { task: Task }) {
  if (task.state) {
    return (
      <span className="flex items-center gap-1 text-xs text-muted-foreground shrink-0">
        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: task.state.color }} />
        {task.state.name}
      </span>
    )
  }
  return (
    <Badge variant="outline" className="text-xs shrink-0">
      {TASK_STATUS_LABELS[task.status]}
    </Badge>
  )
}

export function BacklogPage() {
  const { orgId = "", projectId = "" } = useParams<{ orgId: string; projectId: string }>()

  const { data: project } = useProject(orgId, projectId)
  const { data: allTasks = [] } = useTasks(orgId, projectId)
  const { data: sprints = [] } = useSprints(orgId, projectId)
  const { mutate: updateTask } = useUpdateTask(orgId, projectId)
  const openTaskPanel = useAppStore((s) => s.openTaskPanel)
  const membership = useAppStore((s) => s.activeMembership)
  const canCreate = membership?.role && ["member", "admin", "owner"].includes(membership.role)

  const [expandedSprints, setExpandedSprints] = useState<Set<string>>(new Set())
  const [assignToSprint, setAssignToSprint] = useState<string>("")
  const [backlogDragOver, setBacklogDragOver] = useState(false)

  const handleBacklogDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setBacklogDragOver(false)
    const taskId = e.dataTransfer.getData("text/task-id")
    if (taskId) updateTask({ taskId, data: { sprint_id: null } })
  }, [updateTask])

  // Group tasks by sprint
  const { sprintTasks, backlogTasks } = useMemo(() => {
    const sprintMap = new Map<string, Task[]>()
    const backlog: Task[] = []

    for (const task of allTasks) {
      if (task.sprint_id) {
        const list = sprintMap.get(task.sprint_id) ?? []
        list.push(task)
        sprintMap.set(task.sprint_id, list)
      } else {
        backlog.push(task)
      }
    }

    return { sprintTasks: sprintMap, backlogTasks: backlog }
  }, [allTasks])

  // Sort sprints: active first, then backlog, then closed
  const sortedSprints = useMemo(() => {
    const order = { active: 0, backlog: 1, closed: 2 }
    return [...sprints].sort((a, b) => order[a.status] - order[b.status])
  }, [sprints])

  function toggleSprint(sprintId: string) {
    setExpandedSprints((prev) => {
      const next = new Set(prev)
      if (next.has(sprintId)) next.delete(sprintId)
      else next.add(sprintId)
      return next
    })
  }

  function handleMoveTask(taskId: string, sprintId: string | null) {
    updateTask({ taskId, data: { sprint_id: sprintId } })
  }

  function handleAssignSelected(taskId: string) {
    if (assignToSprint) {
      updateTask({ taskId, data: { sprint_id: assignToSprint } })
    }
  }

  return (
    <div className="flex flex-col h-full gap-4">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h1 className="text-xl font-semibold">{project?.name ?? "Backlog"}</h1>
          <p className="text-sm text-muted-foreground">
            Plan sprints and manage your backlog
          </p>
        </div>
        <div className="flex items-center gap-2">
          {canCreate && (
            <>
              <CreateSprintDialog orgId={orgId} projectId={projectId}>
                <Button size="sm" variant="outline">
                  <Plus className="h-4 w-4 mr-1" />
                  New Sprint
                </Button>
              </CreateSprintDialog>
              <CreateTaskDialog orgId={orgId} projectId={projectId}>
                <Button size="sm">
                  <Plus className="h-4 w-4 mr-1" />
                  New Task
                </Button>
              </CreateTaskDialog>
            </>
          )}
        </div>
      </div>

      {/* Sprints */}
      <div className="space-y-3">
        {sortedSprints.map((sprint) => (
          <SprintCard
            key={sprint.id}
            sprint={sprint}
            tasks={sprintTasks.get(sprint.id) ?? []}
            orgId={orgId}
            projectId={projectId}
            expanded={expandedSprints.has(sprint.id) || sprint.status === "active"}
            onToggle={() => toggleSprint(sprint.id)}
            onMoveTask={handleMoveTask}
          />
        ))}
      </div>

      {/* Backlog */}
      <div
        className={cn("rounded-lg border bg-card transition-colors", backlogDragOver && "ring-2 ring-primary/40")}
        onDragOver={(e) => { e.preventDefault(); setBacklogDragOver(true) }}
        onDragLeave={() => setBacklogDragOver(false)}
        onDrop={handleBacklogDrop}
      >
        <div className="flex items-center gap-2 px-4 py-3">
          <h3 className="font-medium text-sm flex-1">
            Backlog
            <span className="ml-2 text-muted-foreground">
              ({backlogTasks.length} task{backlogTasks.length !== 1 ? "s" : ""})
            </span>
          </h3>
          {sprints.length > 0 && (
            <Select value={assignToSprint} onValueChange={setAssignToSprint}>
              <SelectTrigger className="w-40 h-8 text-xs">
                <SelectValue placeholder="Move to sprint…" />
              </SelectTrigger>
              <SelectContent>
                {sprints
                  .filter((s) => s.status !== "closed")
                  .map((s) => (
                    <SelectItem key={s.id} value={s.id}>
                      {s.name}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
          )}
        </div>
        <div className="border-t divide-y">
          {backlogTasks.length === 0 && (
            <p className="px-4 py-6 text-sm text-muted-foreground text-center">
              No tasks in the backlog. Create a task to get started.
            </p>
          )}
          {backlogTasks.map((task) => (
            <div
              key={task.id}
              draggable
              onDragStart={(e) => { e.dataTransfer.setData("text/task-id", task.id); e.dataTransfer.effectAllowed = "move" }}
              className="flex items-center gap-3 px-4 py-2 hover:bg-accent/50 cursor-grab active:cursor-grabbing text-sm"
              onClick={() => openTaskPanel(task.id)}
            >
              <IssueTypeIcon type={task.issue_type} className="h-4 w-4 shrink-0" />
              <span className="flex-1 truncate">{task.title}</span>
              <StateChip task={task} />
              {task.story_points != null && (
                <span className="text-xs text-muted-foreground">{task.story_points} pts</span>
              )}
              {assignToSprint && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 text-xs"
                  onClick={(e) => { e.stopPropagation(); handleAssignSelected(task.id) }}
                >
                  Add to sprint
                </Button>
              )}
            </div>
          ))}
        </div>
      </div>

      <TaskDetailPanel orgId={orgId} projectId={projectId} />
    </div>
  )
}
