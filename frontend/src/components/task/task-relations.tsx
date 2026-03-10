import { useState } from "react"
import { Plus, X, ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select"
import { IssueTypeIcon } from "./issue-type-icon"
import { useCreateTaskLink, useDeleteTaskLink } from "@/hooks/use-task-links"
import { useTasks } from "@/hooks/use-tasks"
import { useAppStore } from "@/store/app-store"
import type { TaskLinkOut, LinkType } from "@/types/task"
import { LINK_TYPE_LABELS } from "@/types/task"
import { cn } from "@/lib/utils"

interface TaskRelationsProps {
  orgId: string
  projectId: string
  taskId: string
  links: TaskLinkOut[]
  canEdit: boolean
}

export function TaskRelations({ orgId, projectId, taskId, links, canEdit }: TaskRelationsProps) {
  const [adding, setAdding] = useState(false)
  const [linkType, setLinkType] = useState<LinkType>("relates_to")
  const [search, setSearch] = useState("")
  const openTaskPanel = useAppStore((s) => s.openTaskPanel)

  const { mutate: createLink, isPending: creating } = useCreateTaskLink(orgId, projectId, taskId)
  const { mutate: deleteLink } = useDeleteTaskLink(orgId, projectId, taskId)

  // Load all tasks in project for search
  const { data: allTasks = [] } = useTasks(orgId, projectId)
  const filteredTasks = allTasks.filter(
    (t) =>
      t.id !== taskId &&
      t.title.toLowerCase().includes(search.toLowerCase()) &&
      !links.some((l) => l.source_task.id === t.id || l.target_task.id === t.id)
  )

  function handleCreate(targetId: string) {
    createLink(
      { target_task_id: targetId, link_type: linkType },
      { onSuccess: () => { setAdding(false); setSearch("") } }
    )
  }

  if (links.length === 0 && !canEdit) return null

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium text-muted-foreground">Relations</p>
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

      {/* Existing links */}
      <div className="space-y-0.5">
        {links.map((link) => {
          // Determine the "other" task
          const isSource = link.source_task.id === taskId
          const otherTask = isSource ? link.target_task : link.source_task

          return (
            <div
              key={link.id}
              className="group flex items-center gap-2 rounded px-1.5 py-1 text-xs hover:bg-accent transition-colors"
            >
              <span className="text-muted-foreground shrink-0 w-24 truncate">
                {LINK_TYPE_LABELS[link.link_type]}
              </span>
              <ArrowRight className="h-3 w-3 text-muted-foreground shrink-0" />
              <button
                className="flex items-center gap-1.5 truncate hover:underline"
                onClick={() => openTaskPanel(otherTask.id)}
              >
                <IssueTypeIcon type={otherTask.issue_type} className="h-3 w-3" />
                <span className={cn(otherTask.status === "done" && "line-through text-muted-foreground")}>
                  {otherTask.title}
                </span>
              </button>
              {canEdit && (
                <button
                  className="ml-auto opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-all"
                  onClick={() => deleteLink(link.id)}
                >
                  <X className="h-3 w-3" />
                </button>
              )}
            </div>
          )
        })}
      </div>

      {/* Add relation form */}
      {adding && (
        <div className="space-y-2 rounded border p-2">
          <Select value={linkType} onValueChange={(v) => setLinkType(v as LinkType)}>
            <SelectTrigger className="h-7 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {(Object.entries(LINK_TYPE_LABELS) as [LinkType, string][]).map(([v, label]) => (
                <SelectItem key={v} value={v}>{label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Input
            autoFocus
            placeholder="Search tasks…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-7 text-xs"
            onKeyDown={(e) => {
              if (e.key === "Escape") { setAdding(false); setSearch("") }
            }}
          />
          {search && (
            <div className="max-h-32 overflow-y-auto space-y-0.5">
              {filteredTasks.slice(0, 8).map((t) => (
                <button
                  key={t.id}
                  className="flex items-center gap-1.5 w-full rounded px-1.5 py-1 text-xs hover:bg-accent transition-colors text-left"
                  onClick={() => handleCreate(t.id)}
                  disabled={creating}
                >
                  <IssueTypeIcon type={t.issue_type} className="h-3 w-3" />
                  <span className="truncate">{t.title}</span>
                </button>
              ))}
              {filteredTasks.length === 0 && (
                <p className="text-xs text-muted-foreground px-1.5 py-1">No matching tasks</p>
              )}
            </div>
          )}
          <div className="flex justify-end">
            <Button variant="ghost" size="sm" className="h-6 text-xs" onClick={() => { setAdding(false); setSearch("") }}>
              Cancel
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
