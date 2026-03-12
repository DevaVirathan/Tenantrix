import { useState } from "react"
import { useParams } from "react-router-dom"
import { Plus, Box, Trash2, ChevronDown, ChevronRight } from "lucide-react"
import { format } from "date-fns"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import {
  Dialog, DialogContent, DialogDescription, DialogFooter,
  DialogHeader, DialogTitle, DialogTrigger,
} from "@/components/ui/dialog"
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select"
import { ConfirmDialog } from "@/components/shared/confirm-dialog"
import { useProject } from "@/hooks/use-projects"
import { useModules, useCreateModule, useUpdateModule, useDeleteModule } from "@/hooks/use-modules"
import { useTasks } from "@/hooks/use-tasks"
import { useAppStore } from "@/store/app-store"
import { hasRole } from "@/lib/rbac"
import { TaskDetailPanel } from "@/components/task/task-detail-panel"
import { IssueTypeIcon } from "@/components/task/issue-type-icon"
import type { Module } from "@/types/module"

export function ModulesPage() {
  const { orgId = "", projectId = "" } = useParams<{ orgId: string; projectId: string }>()
  const { data: project } = useProject(orgId, projectId)
  const { data: modules = [], isLoading } = useModules(orgId, projectId)
  const { data: tasks = [] } = useTasks(orgId, projectId)
  const membership = useAppStore((s) => s.activeMembership)
  const canManage = hasRole(membership?.role, "member")
  const openTaskPanel = useAppStore((s) => s.openTaskPanel)

  const [expandedModules, setExpandedModules] = useState<Set<string>>(new Set())

  function toggleExpand(id: string) {
    setExpandedModules((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const moduleTasks = (moduleId: string) => tasks.filter((t) => t.module_id === moduleId)

  return (
    <div className="flex flex-col h-full gap-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h1 className="text-xl font-semibold">{project?.name ?? "Modules"}</h1>
          <p className="text-sm text-muted-foreground">Group related tasks into feature modules</p>
        </div>
        {canManage && <CreateModuleDialog orgId={orgId} projectId={projectId} />}
      </div>

      {isLoading && (
        <div className="flex items-center justify-center h-40">
          <p className="text-muted-foreground">Loading modules…</p>
        </div>
      )}

      {!isLoading && modules.length === 0 && (
        <div className="flex flex-col items-center justify-center h-40 gap-2 text-muted-foreground">
          <Box className="h-8 w-8" />
          <p className="text-sm">No modules yet. Create one to group related tasks.</p>
        </div>
      )}

      <div className="space-y-3">
        {modules.map((mod) => (
          <ModuleCard
            key={mod.id}
            module={mod}
            tasks={moduleTasks(mod.id)}
            expanded={expandedModules.has(mod.id)}
            onToggle={() => toggleExpand(mod.id)}
            onTaskClick={openTaskPanel}
            orgId={orgId}
            projectId={projectId}
            canManage={canManage}
          />
        ))}
      </div>

      <TaskDetailPanel orgId={orgId} projectId={projectId} />
    </div>
  )
}

// ── Module Card ────────────────────────────────────────────────────────────────

interface ModuleCardProps {
  module: Module
  tasks: { id: string; title: string; issue_type: string; state?: { name: string; color: string; group: string } | null }[]
  expanded: boolean
  onToggle: () => void
  onTaskClick: (id: string) => void
  orgId: string
  projectId: string
  canManage: boolean
}

function ModuleCard({ module: mod, tasks, expanded, onToggle, onTaskClick, orgId, projectId, canManage }: ModuleCardProps) {
  const { mutate: updateModule } = useUpdateModule(orgId, projectId)
  const { mutate: deleteModule } = useDeleteModule(orgId, projectId)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const pct = mod.task_count > 0 ? Math.round((mod.done_count / mod.task_count) * 100) : 0

  return (
    <div className="rounded-lg border bg-card">
      <div className="flex items-center gap-3 px-4 py-3">
        <button onClick={onToggle} className="shrink-0 text-muted-foreground hover:text-foreground">
          {expanded
            ? <ChevronDown className="h-4 w-4" />
            : <ChevronRight className="h-4 w-4" />
          }
        </button>
        <Box className="h-4 w-4 text-muted-foreground shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-sm truncate">{mod.name}</span>
            <Badge variant={mod.status === "active" ? "default" : "secondary"} className="text-[10px] h-5">
              {mod.status}
            </Badge>
          </div>
          {mod.description && (
            <p className="text-xs text-muted-foreground truncate mt-0.5">{mod.description}</p>
          )}
        </div>
        <div className="flex items-center gap-3 shrink-0">
          {mod.start_date && mod.end_date && (
            <span className="text-[10px] text-muted-foreground hidden sm:block">
              {format(new Date(mod.start_date), "MMM d")} – {format(new Date(mod.end_date), "MMM d")}
            </span>
          )}
          <div className="flex items-center gap-2 w-32">
            <Progress value={pct} className="h-1.5 flex-1" />
            <span className="text-[10px] text-muted-foreground w-12 text-right">
              {mod.done_count}/{mod.task_count}
            </span>
          </div>
          {canManage && (
            <Select
              value={mod.status}
              onValueChange={(v) => updateModule({ moduleId: mod.id, data: { status: v } })}
            >
              <SelectTrigger className="h-7 w-20 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="closed">Closed</SelectItem>
              </SelectContent>
            </Select>
          )}
          {canManage && (
            <>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 text-muted-foreground hover:text-destructive"
                onClick={() => setConfirmDelete(true)}
              >
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
              <ConfirmDialog
                open={confirmDelete}
                onOpenChange={setConfirmDelete}
                title="Delete module?"
                description={`"${mod.name}" will be deleted. Tasks in this module will be unlinked, not deleted.`}
                onConfirm={() => { deleteModule(mod.id); setConfirmDelete(false) }}
              />
            </>
          )}
        </div>
      </div>

      {expanded && (
        <div className="border-t px-4 py-2">
          {tasks.length === 0 ? (
            <p className="text-xs text-muted-foreground py-2 text-center">No tasks in this module.</p>
          ) : (
            <div className="space-y-0.5">
              {tasks.map((task) => (
                <button
                  key={task.id}
                  className="flex items-center gap-2 w-full rounded px-2 py-1.5 text-xs hover:bg-accent transition-colors text-left"
                  onClick={() => onTaskClick(task.id)}
                >
                  <IssueTypeIcon type={task.issue_type as "task"} className="h-3.5 w-3.5 shrink-0" />
                  {task.state && (
                    <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: task.state.color }} />
                  )}
                  <span className="truncate">{task.title}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Create Module Dialog ───────────────────────────────────────────────────────

function CreateModuleDialog({ orgId, projectId }: { orgId: string; projectId: string }) {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [startDate, setStartDate] = useState("")
  const [endDate, setEndDate] = useState("")
  const { mutate: createModule, isPending } = useCreateModule(orgId, projectId)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim()) return
    createModule(
      {
        name: name.trim(),
        description: description.trim() || null,
        start_date: startDate ? new Date(startDate).toISOString() : null,
        end_date: endDate ? new Date(endDate).toISOString() : null,
      },
      {
        onSuccess: () => {
          setName("")
          setDescription("")
          setStartDate("")
          setEndDate("")
          setOpen(false)
        },
      },
    )
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm"><Plus className="h-4 w-4 mr-1" /> New module</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Create Module</DialogTitle>
          <DialogDescription>Group related tasks into a feature module.</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm font-medium">Name</label>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Module name…" />
          </div>
          <div>
            <label className="text-sm font-medium">Description <span className="text-muted-foreground">(optional)</span></label>
            <Input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Brief description…" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm font-medium">Start date</label>
              <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
            </div>
            <div>
              <label className="text-sm font-medium">End date</label>
              <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={isPending || !name.trim()}>
              {isPending ? "Creating…" : "Create Module"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
