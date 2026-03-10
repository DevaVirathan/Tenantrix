import { useState } from "react"
import { Plus, CheckCircle2, Circle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { IssueTypeIcon } from "./issue-type-icon"
import { useCreateTask } from "@/hooks/use-tasks"
import { useAppStore } from "@/store/app-store"
import type { TaskSummary } from "@/types/task"
import { cn } from "@/lib/utils"

interface SubtaskListProps {
  orgId: string
  projectId: string
  parentTaskId: string
  subtasks: TaskSummary[]
  canEdit: boolean
}

export function SubtaskList({ orgId, projectId, parentTaskId, subtasks, canEdit }: SubtaskListProps) {
  const [adding, setAdding] = useState(false)
  const [title, setTitle] = useState("")
  const openTaskPanel = useAppStore((s) => s.openTaskPanel)
  const { mutate: createTask, isPending } = useCreateTask(orgId, projectId)

  function handleAdd() {
    const trimmed = title.trim()
    if (!trimmed) return
    createTask(
      {
        title: trimmed,
        status: "todo",
        priority: "medium",
        issue_type: "subtask",
        parent_task_id: parentTaskId,
      },
      {
        onSuccess: () => {
          setTitle("")
          setAdding(false)
        },
      }
    )
  }

  const doneCount = subtasks.filter((s) => s.status === "done").length

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium text-muted-foreground">
          Sub-tasks {subtasks.length > 0 && `(${doneCount}/${subtasks.length})`}
        </p>
        {canEdit && !adding && (
          <Button
            variant="ghost"
            size="sm"
            className="h-6 text-xs gap-1 text-muted-foreground"
            onClick={() => setAdding(true)}
          >
            <Plus className="h-3 w-3" />
            Add
          </Button>
        )}
      </div>

      {/* Progress bar */}
      {subtasks.length > 0 && (
        <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-emerald-500 rounded-full transition-all"
            style={{ width: `${(doneCount / subtasks.length) * 100}%` }}
          />
        </div>
      )}

      {/* Subtask items */}
      <div className="space-y-0.5">
        {subtasks.map((sub) => (
          <button
            key={sub.id}
            className="flex items-center gap-2 w-full rounded px-1.5 py-1 text-xs hover:bg-accent transition-colors text-left"
            onClick={() => openTaskPanel(sub.id)}
          >
            {sub.status === "done" ? (
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
            ) : (
              <Circle className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
            )}
            <IssueTypeIcon type={sub.issue_type} className="h-3 w-3" />
            <span className={cn("truncate", sub.status === "done" && "line-through text-muted-foreground")}>
              {sub.title}
            </span>
          </button>
        ))}
      </div>

      {/* Inline add form */}
      {adding && (
        <div className="flex items-center gap-1.5">
          <Input
            autoFocus
            placeholder="Sub-task title…"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="h-7 text-xs"
            onKeyDown={(e) => {
              if (e.key === "Enter") handleAdd()
              if (e.key === "Escape") { setAdding(false); setTitle("") }
            }}
            disabled={isPending}
          />
          <Button size="sm" className="h-7 text-xs" onClick={handleAdd} disabled={isPending || !title.trim()}>
            {isPending ? "…" : "Add"}
          </Button>
        </div>
      )}
    </div>
  )
}
