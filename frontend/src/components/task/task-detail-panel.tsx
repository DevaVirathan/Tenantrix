import { useEffect, useRef, useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import {
  X, Trash2, Paperclip, UserCircle2, Eye, EyeOff,
  AlertCircle, ArrowDown, ArrowRight, ArrowUp, CalendarDays,
  Hexagon, Layers, Timer, Box,
} from "lucide-react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Separator } from "@/components/ui/separator"
import { Textarea } from "@/components/ui/textarea"
import { RichTextEditor, RichTextViewer } from "@/components/shared/rich-text-editor"
import { DatePicker } from "@/components/shared/date-picker"
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select"
import { AssigneePicker } from "./assignee-picker"
import { IssueTypeIcon } from "./issue-type-icon"
import { LabelPicker } from "./label-picker"
import { SubtaskList } from "./subtask-list"
import { TaskRelations } from "./task-relations"
import { useTask, useUpdateTask, useDeleteTask } from "@/hooks/use-tasks"
import { useProject } from "@/hooks/use-projects"
import { useSprints } from "@/hooks/use-sprints"
import { useModules } from "@/hooks/use-modules"
import { useProjectStates } from "@/hooks/use-project-states"
import { CommentThread } from "./comment-thread"
import { AttachmentList } from "./attachment-list"
import { useWatchers, useToggleWatch } from "@/hooks/use-watchers"
import { useAppStore } from "@/store/app-store"
import { useMembers } from "@/hooks/use-members"
import { hasRole } from "@/lib/rbac"
import { updateTaskSchema, type UpdateTaskValues } from "@/validations/task.schema"
import type { TaskPriority, IssueType } from "@/types/task"
import { TASK_PRIORITY_LABELS, ISSUE_TYPE_LABELS } from "@/types/task"
import { cn } from "@/lib/utils"

interface TaskDetailPanelProps {
  orgId: string
  projectId: string
}

// ── Priority colours / icons ──────────────────────────────────────────────────
const PRIORITY_CONFIG: Record<TaskPriority, { icon: React.ElementType; className: string }> = {
  low:    { icon: ArrowDown,   className: "text-gray-400" },
  medium: { icon: ArrowRight,  className: "text-yellow-400" },
  high:   { icon: ArrowUp,     className: "text-orange-400" },
  urgent: { icon: AlertCircle, className: "text-red-400" },
}

function initials(name: string) {
  return name.split(" ").map((w) => w[0]).join("").toUpperCase().slice(0, 2)
}

// ── Property row ──────────────────────────────────────────────────────────────
function PropRow({
  icon: Icon,
  label,
  children,
}: {
  icon: React.ElementType
  label: string
  children: React.ReactNode
}) {
  return (
    <div className="flex items-start gap-2 py-1.5">
      <div className="flex items-center gap-1.5 w-28 shrink-0 text-xs text-muted-foreground pt-1.5">
        <Icon className="h-3.5 w-3.5 shrink-0" />
        <span>{label}</span>
      </div>
      <div className="flex-1 min-w-0">{children}</div>
    </div>
  )
}

export function TaskDetailPanel({ orgId, projectId }: TaskDetailPanelProps) {
  const taskPanelOpen = useAppStore((s) => s.taskPanelOpen)
  const activeTaskId = useAppStore((s) => s.activeTaskId)
  const closeTaskPanel = useAppStore((s) => s.closeTaskPanel)
  const openTaskPanel = useAppStore((s) => s.openTaskPanel)
  const membership = useAppStore((s) => s.activeMembership)
  const user = useAppStore((s) => s.user)

  const canEdit = hasRole(membership?.role, "member")
  const canDelete = hasRole(membership?.role, "admin")

  const { data: project } = useProject(orgId, projectId)
  const { data: task, isLoading } = useTask(orgId, activeTaskId ?? "")
  const { mutate: updateTask, isPending: isUpdating } = useUpdateTask(orgId, projectId)
  const { mutate: deleteTask, isPending: isDeleting } = useDeleteTask(orgId, projectId)
  const { data: members = [] } = useMembers(orgId)
  const { data: sprints = [] } = useSprints(orgId, projectId)
  const { data: modules = [] } = useModules(orgId, projectId)
  const { data: projectStates = [] } = useProjectStates(orgId, projectId)
  const { data: watchers = [] } = useWatchers(orgId, activeTaskId ?? "")
  const { watch: watchTask, unwatch: unwatchTask } = useToggleWatch(orgId, activeTaskId ?? "")
  const isWatching = watchers.some((w) => w.user_id === user?.id)

  // ── Inline title editing ──────────────────────────────────────────────────
  const [editingTitle, setEditingTitle] = useState(false)
  const [titleDraft, setTitleDraft] = useState("")
  const titleRef = useRef<HTMLTextAreaElement>(null)

  // ── Inline description editing ────────────────────────────────────────────
  const [editingDesc, setEditingDesc] = useState(false)
  const [descDraft, setDescDraft] = useState("")
  const descRef = useRef<HTMLTextAreaElement>(null)

  const form = useForm<UpdateTaskValues>({
    resolver: zodResolver(updateTaskSchema),
    defaultValues: { title: "", description: "", status: "todo", priority: "medium" },
  })

  useEffect(() => {
    if (task) {
      setTitleDraft(task.title)
      setDescDraft(task.description ?? "")
      form.reset({
        title: task.title,
        description: task.description ?? "",
        status: task.status,
        priority: task.priority,
        assignee_user_id: task.assignee_user_id,
      })
    }
  }, [task, form])

  // Focus textarea when entering edit mode
  useEffect(() => {
    if (editingTitle) setTimeout(() => titleRef.current?.focus(), 50)
  }, [editingTitle])
  useEffect(() => {
    if (editingDesc) setTimeout(() => descRef.current?.focus(), 50)
  }, [editingDesc])

  function saveTitle() {
    const trimmed = titleDraft.trim()
    if (!trimmed || trimmed === task?.title) { setEditingTitle(false); return }
    updateTask({ taskId: task!.id, data: { title: trimmed } })
    setEditingTitle(false)
  }

  function saveDesc() {
    const trimmed = descDraft.trim() || null
    if (trimmed === (task?.description ?? null)) { setEditingDesc(false); return }
    updateTask({ taskId: task!.id, data: { description: trimmed } })
    setEditingDesc(false)
  }

  function handlePropChange(data: UpdateTaskValues) {
    if (!task) return
    updateTask({ taskId: task.id, data })
  }

  function handleDelete() {
    if (!task) return
    if (!confirm(`Delete task "${task.title}"? This cannot be undone.`)) return
    deleteTask(task.id, { onSuccess: closeTaskPanel })
  }

  const assignee = task?.assignee_user_id
    ? members.find((m) => m.user_id === task.assignee_user_id)
    : null
  const assigneeName = assignee ? (assignee.full_name ?? assignee.email ?? "Unassigned") : null

  const createdByMember = task?.created_by_user_id
    ? members.find((m) => m.user_id === task.created_by_user_id)
    : null
  const createdByName = createdByMember
    ? (createdByMember.full_name ?? createdByMember.email ?? "Unknown")
    : null

  const priorities = Object.keys(TASK_PRIORITY_LABELS) as TaskPriority[]

  if (!taskPanelOpen) return null

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/20"
        onClick={closeTaskPanel}
        aria-hidden="true"
      />

      {/* Panel */}
      <div
        role="dialog"
        aria-label={task ? `Task: ${task.title}` : "Task details"}
        className="fixed inset-y-0 right-0 z-50 flex w-full max-w-4xl shadow-2xl bg-background border-l animate-in slide-in-from-right duration-200"
      >

        {/* ── Close button ── */}
        <button
          aria-label="Close task panel"
          onClick={closeTaskPanel}
          className="absolute top-3 right-3 z-10 rounded-md p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
        >
          <X className="h-4 w-4" />
        </button>

        {isLoading || !task ? (
          <div className="flex-1 p-8 space-y-4">
            <Skeleton className="h-8 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-40 w-full" />
          </div>
        ) : (
          <div className="flex flex-1 overflow-hidden">

            {/* ═══════════════════════════════════════════════════════════════
                LEFT — main content (title · description · actions · activity)
            ════════════════════════════════════════════════════════════════ */}
            <div className="flex flex-col flex-1 overflow-y-auto px-8 py-6 gap-5">

              {/* Issue ID */}
              {project?.identifier && task.sequence_id != null && (
                <p className="text-xs text-muted-foreground font-medium">
                  {project.identifier}-{task.sequence_id}
                </p>
              )}

              {/* Title */}
              {editingTitle ? (
                <Textarea
                  ref={titleRef}
                  value={titleDraft}
                  onChange={(e) => setTitleDraft(e.target.value)}
                  className="text-xl font-semibold resize-none border-0 shadow-none focus-visible:ring-1 p-0 min-h-0 leading-snug"
                  onBlur={saveTitle}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); saveTitle() }
                    if (e.key === "Escape") { setTitleDraft(task.title); setEditingTitle(false) }
                  }}
                  rows={2}
                  disabled={!canEdit}
                />
              ) : (
                <h1
                  className={cn(
                    "text-xl font-semibold leading-snug pr-8",
                    canEdit && "cursor-text hover:bg-accent/50 rounded px-1 -mx-1 py-0.5 transition-colors"
                  )}
                  onClick={() => canEdit && setEditingTitle(true)}
                >
                  {task.title}
                </h1>
              )}

              {/* Description */}
              {editingDesc ? (
                <div onBlur={(e) => {
                  if (!e.currentTarget.contains(e.relatedTarget)) saveDesc()
                }}>
                  <RichTextEditor
                    content={descDraft}
                    onChange={setDescDraft}
                    placeholder="Add a description…"
                    editable={canEdit}
                  />
                  <div className="flex justify-end gap-2 mt-2">
                    <Button variant="ghost" size="sm" onClick={() => { setDescDraft(task.description ?? ""); setEditingDesc(false) }}>
                      Cancel
                    </Button>
                    <Button size="sm" onClick={saveDesc}>Save</Button>
                  </div>
                </div>
              ) : (
                <div
                  className={cn(
                    "text-sm text-muted-foreground rounded px-1 -mx-1 py-1 min-h-6",
                    canEdit && "cursor-text hover:bg-accent/50 transition-colors"
                  )}
                  onClick={() => canEdit && setEditingDesc(true)}
                >
                  {task.description
                    ? <RichTextViewer content={task.description} />
                    : <span className="italic">Add a description…</span>
                  }
                </div>
              )}

              {/* Parent breadcrumb */}
              {task.parent && (
                <button
                  className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
                  onClick={() => openTaskPanel(task.parent!.id)}
                >
                  <IssueTypeIcon type={task.parent.issue_type} className="h-3 w-3" />
                  <span className="truncate max-w-xs">{task.parent.title}</span>
                  <span className="text-muted-foreground/60">/ sub-task</span>
                </button>
              )}

              {/* Sub-tasks */}
              <SubtaskList
                orgId={orgId}
                projectId={projectId}
                parentTaskId={task.id}
                subtasks={task.subtasks}
                canEdit={canEdit}
              />

              {/* Relations */}
              <TaskRelations
                orgId={orgId}
                projectId={projectId}
                taskId={task.id}
                links={task.links}
                canEdit={canEdit}
              />

              {/* Attachments */}
              <AttachmentList orgId={orgId} taskId={task.id} canEdit={canEdit} />

              <Separator />

              {/* Activity + Comments */}
              <CommentThread orgId={orgId} taskId={task.id} />

              {/* Delete (bottom of left column) */}
              {canDelete && (
                <>
                  <Separator className="mt-4" />
                  <div className="pb-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="gap-2 text-destructive hover:text-destructive hover:bg-destructive/10"
                      onClick={handleDelete}
                      disabled={isDeleting}
                    >
                      <Trash2 className="h-4 w-4" />
                      {isDeleting ? "Deleting…" : "Delete work item"}
                    </Button>
                  </div>
                </>
              )}
            </div>

            {/* ═══════════════════════════════════════════════════════════════
                RIGHT — properties panel
            ════════════════════════════════════════════════════════════════ */}
            <div className="w-64 shrink-0 border-l bg-muted/20 overflow-y-auto px-4 py-6 flex flex-col gap-1">
              <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                Properties
              </p>

              {/* State (dynamic project states) */}
              <PropRow icon={CalendarDays} label="State">
                <Select
                  value={task.state_id ?? ""}
                  onValueChange={(v) => handlePropChange({ state_id: v })}
                  disabled={!canEdit || isUpdating}
                >
                  <SelectTrigger className="h-7 text-xs border-0 bg-transparent shadow-none px-1 hover:bg-accent focus:ring-0 w-full justify-start gap-1.5">
                    {task.state && (
                      <span
                        className="inline-block h-2 w-2 rounded-full shrink-0"
                        style={{ backgroundColor: task.state.color }}
                      />
                    )}
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {projectStates.map((s) => (
                      <SelectItem key={s.id} value={s.id}>
                        <span className="flex items-center gap-2">
                          <span
                            className="inline-block h-2 w-2 rounded-full"
                            style={{ backgroundColor: s.color }}
                          />
                          {s.name}
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </PropRow>

              {/* Assignees */}
              <PropRow icon={UserCircle2} label="Assignees">
                {canEdit ? (
                  <AssigneePicker
                    orgId={orgId}
                    value={task.assignee_user_id}
                    onChange={(userId) => handlePropChange({ assignee_user_id: userId })}
                    disabled={isUpdating}
                    compact
                  />
                ) : assigneeName ? (
                  <span className="flex items-center gap-1.5 text-xs px-1">
                    <Avatar className="h-5 w-5">
                      <AvatarFallback className="text-[10px]">{initials(assigneeName)}</AvatarFallback>
                    </Avatar>
                    {assigneeName}
                  </span>
                ) : (
                  <span className="text-xs text-muted-foreground px-1">None</span>
                )}
              </PropRow>

              {/* Priority */}
              <PropRow icon={AlertCircle} label="Priority">
                <Select
                  value={task.priority}
                  onValueChange={(v) => handlePropChange({ priority: v as TaskPriority })}
                  disabled={!canEdit || isUpdating}
                >
                  <SelectTrigger className="h-7 text-xs border-0 bg-transparent shadow-none px-1 hover:bg-accent focus:ring-0 w-full justify-start gap-1.5">
                    {(() => {
                      const { icon: Icon, className } = PRIORITY_CONFIG[task.priority]
                      return <Icon className={cn("h-3.5 w-3.5 shrink-0", className)} />
                    })()}
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {priorities.map((p) => {
                      const { icon: Icon, className } = PRIORITY_CONFIG[p]
                      return (
                        <SelectItem key={p} value={p}>
                          <span className="flex items-center gap-2">
                            <Icon className={cn("h-3.5 w-3.5", className)} />
                            {TASK_PRIORITY_LABELS[p]}
                          </span>
                        </SelectItem>
                      )
                    })}
                  </SelectContent>
                </Select>
              </PropRow>

              {/* Issue Type */}
              <PropRow icon={Layers} label="Type">
                <Select
                  value={task.issue_type}
                  onValueChange={(v) => handlePropChange({ issue_type: v as IssueType })}
                  disabled={!canEdit || isUpdating}
                >
                  <SelectTrigger className="h-7 text-xs border-0 bg-transparent shadow-none px-1 hover:bg-accent focus:ring-0 w-full justify-start gap-1.5">
                    <IssueTypeIcon type={task.issue_type} />
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {(Object.entries(ISSUE_TYPE_LABELS) as [IssueType, string][]).map(([v, label]) => (
                      <SelectItem key={v} value={v}>
                        <span className="flex items-center gap-2">
                          <IssueTypeIcon type={v} />
                          {label}
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </PropRow>

              {/* Story Points */}
              <PropRow icon={Hexagon} label="Points">
                {canEdit ? (
                  <input
                    type="number"
                    min={0}
                    max={100}
                    value={task.story_points ?? ""}
                    placeholder="—"
                    className="h-7 w-16 rounded border-0 bg-transparent text-xs px-1 hover:bg-accent focus:ring-1 focus:ring-ring focus:outline-none"
                    onChange={(e) => {
                      const val = e.target.value === "" ? null : Number(e.target.value)
                      handlePropChange({ story_points: val })
                    }}
                    disabled={isUpdating}
                  />
                ) : (
                  <span className="text-xs px-1">{task.story_points ?? "—"}</span>
                )}
              </PropRow>

              {/* Start Date */}
              <PropRow icon={CalendarDays} label="Start date">
                {canEdit ? (
                  <DatePicker
                    value={task.start_date}
                    onChange={(v) => handlePropChange({ start_date: v })}
                    placeholder="Set start date"
                    className="h-7 text-xs border-0 bg-transparent shadow-none px-1 hover:bg-accent"
                  />
                ) : (
                  <span className="text-xs px-1">
                    {task.start_date ? new Date(task.start_date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "—"}
                  </span>
                )}
              </PropRow>

              {/* Due Date */}
              <PropRow icon={CalendarDays} label="Due date">
                {canEdit ? (
                  <DatePicker
                    value={task.due_date}
                    onChange={(v) => handlePropChange({ due_date: v })}
                    placeholder="Set due date"
                    className="h-7 text-xs border-0 bg-transparent shadow-none px-1 hover:bg-accent"
                  />
                ) : (
                  <span className="text-xs px-1">
                    {task.due_date ? new Date(task.due_date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "—"}
                  </span>
                )}
              </PropRow>

              {/* Sprint */}
              <PropRow icon={Timer} label="Sprint">
                {canEdit ? (
                  <Select
                    value={task.sprint_id ?? "__none__"}
                    onValueChange={(v) => handlePropChange({ sprint_id: v === "__none__" ? null : v })}
                    disabled={isUpdating}
                  >
                    <SelectTrigger className="h-7 text-xs border-0 bg-transparent shadow-none px-1 hover:bg-accent focus:ring-0 w-full justify-start gap-1.5">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__none__">No sprint</SelectItem>
                      {sprints
                        .filter((s) => s.status !== "closed")
                        .map((s) => (
                          <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                ) : (
                  <span className="text-xs px-1">
                    {sprints.find((s) => s.id === task.sprint_id)?.name ?? "None"}
                  </span>
                )}
              </PropRow>

              {/* Module */}
              <PropRow icon={Box} label="Module">
                {canEdit ? (
                  <Select
                    value={task.module_id ?? "__none__"}
                    onValueChange={(v) => handlePropChange({ module_id: v === "__none__" ? null : v })}
                    disabled={isUpdating}
                  >
                    <SelectTrigger className="h-7 text-xs border-0 bg-transparent shadow-none px-1 hover:bg-accent focus:ring-0 w-full justify-start gap-1.5">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="__none__">No module</SelectItem>
                      {modules
                        .filter((m) => m.status !== "closed")
                        .map((m) => (
                          <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                ) : (
                  <span className="text-xs px-1">
                    {modules.find((m) => m.id === task.module_id)?.name ?? "None"}
                  </span>
                )}
              </PropRow>

              {/* Created by */}
              <PropRow icon={UserCircle2} label="Created by">
                <span className="flex items-center gap-1.5 text-xs px-1">
                  <Avatar className="h-5 w-5">
                    <AvatarFallback className="text-[10px] bg-primary/20 text-primary">
                      {initials(createdByName ?? "?")}
                    </AvatarFallback>
                  </Avatar>
                  {createdByName ?? "—"}
                </span>
              </PropRow>

              <Separator className="my-2" />

              {/* Labels */}
              <PropRow icon={Paperclip} label="Labels">
                <LabelPicker
                  orgId={orgId}
                  projectId={projectId}
                  taskId={task.id}
                  currentLabels={task.labels}
                  disabled={!canEdit}
                  compact
                />
              </PropRow>

              <Separator className="my-2" />

              {/* Watchers */}
              <PropRow icon={Eye} label="Watchers">
                <div className="flex items-center gap-1 flex-wrap">
                  {watchers.map((w) => (
                    <Avatar key={w.user_id} className="h-5 w-5" title={w.full_name ?? w.email}>
                      <AvatarFallback className="text-[10px]">
                        {initials(w.full_name ?? w.email)}
                      </AvatarFallback>
                    </Avatar>
                  ))}
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 text-xs gap-1 px-1.5"
                    onClick={() => isWatching ? unwatchTask.mutate() : watchTask.mutate()}
                  >
                    {isWatching ? <><EyeOff className="h-3 w-3" /> Unwatch</> : <><Eye className="h-3 w-3" /> Watch</>}
                  </Button>
                </div>
              </PropRow>

              <Separator className="my-2" />

              {/* Created at */}
              <div className="text-xs text-muted-foreground px-1 pt-1">
                <p>Created {new Date(task.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}</p>
                <p className="mt-0.5">Updated {new Date(task.updated_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}</p>
              </div>
            </div>

          </div>
        )}
      </div>
    </>
  )
}
