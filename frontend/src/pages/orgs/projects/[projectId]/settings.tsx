import { useEffect, useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { ArrowLeft, Trash2, Plus, GripVertical, Pencil, Check, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { ProjectStatusBadge } from "@/components/project/project-status-badge"
import { updateProjectSchema, type UpdateProjectValues } from "@/validations/project.schema"
import { useProject, useUpdateProject, useDeleteProject } from "@/hooks/use-projects"
import {
  useProjectStates,
  useCreateProjectState,
  useUpdateProjectState,
  useDeleteProjectState,
} from "@/hooks/use-project-states"
import { useAppStore } from "@/store/app-store"
import { hasRole } from "@/lib/rbac"
import type { ProjectState, StateGroup } from "@/types/project-state"
import { STATE_GROUP_LABELS } from "@/types/project-state"

// Preset colors for state picker
const PRESET_COLORS = [
  "#6b7280", // gray
  "#3b82f6", // blue
  "#8b5cf6", // violet
  "#ec4899", // pink
  "#f59e0b", // amber
  "#10b981", // emerald
  "#ef4444", // red
  "#f97316", // orange
  "#06b6d4", // cyan
  "#84cc16", // lime
]

const STATE_GROUPS: StateGroup[] = ["backlog", "unstarted", "started", "completed", "cancelled"]

// ── Inline state row editor ────────────────────────────────────────────────
interface StateRowProps {
  state: ProjectState
  canEdit: boolean
  orgId: string
  projectId: string
}

function StateRow({ state, canEdit, orgId, projectId }: StateRowProps) {
  const [editing, setEditing] = useState(false)
  const [name, setName] = useState(state.name)
  const [color, setColor] = useState(state.color)
  const [group, setGroup] = useState<StateGroup>(state.group)

  const { mutate: updateState, isPending: isSaving } = useUpdateProjectState(orgId, projectId)
  const { mutate: deleteState, isPending: isDeleting } = useDeleteProjectState(orgId, projectId)

  function save() {
    updateState({ stateId: state.id, data: { name, color, group } })
    setEditing(false)
  }

  function cancel() {
    setName(state.name)
    setColor(state.color)
    setGroup(state.group)
    setEditing(false)
  }

  if (editing) {
    return (
      <div className="flex items-center gap-2 p-2 rounded-lg border bg-muted/30">
        <GripVertical className="h-4 w-4 text-muted-foreground shrink-0" />
        {/* Color picker */}
        <div className="flex gap-1 shrink-0">
          {PRESET_COLORS.map((c) => (
            <button
              key={c}
              type="button"
              className="w-5 h-5 rounded-full border-2 transition-all"
              style={{
                backgroundColor: c,
                borderColor: color === c ? "white" : c,
                outline: color === c ? `2px solid ${c}` : "none",
              }}
              onClick={() => setColor(c)}
            />
          ))}
        </div>
        <Input
          className="h-7 text-sm flex-1"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") save(); if (e.key === "Escape") cancel() }}
          autoFocus
        />
        <Select value={group} onValueChange={(v) => setGroup(v as StateGroup)}>
          <SelectTrigger className="h-7 w-32 text-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {STATE_GROUPS.map((g) => (
              <SelectItem key={g} value={g} className="text-xs">
                {STATE_GROUP_LABELS[g]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button size="icon" variant="ghost" className="h-7 w-7" onClick={save} disabled={isSaving}>
          <Check className="h-3.5 w-3.5" />
        </Button>
        <Button size="icon" variant="ghost" className="h-7 w-7" onClick={cancel}>
          <X className="h-3.5 w-3.5" />
        </Button>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/30 group">
      <GripVertical className="h-4 w-4 text-muted-foreground shrink-0" />
      <span
        className="w-3 h-3 rounded-full shrink-0"
        style={{ backgroundColor: state.color }}
      />
      <span className="text-sm font-medium flex-1">{state.name}</span>
      <Badge variant="outline" className="text-xs capitalize shrink-0">
        {STATE_GROUP_LABELS[state.group]}
      </Badge>
      {state.is_default && (
        <Badge variant="secondary" className="text-xs shrink-0">Default</Badge>
      )}
      {canEdit && (
        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button
            size="icon"
            variant="ghost"
            className="h-7 w-7"
            onClick={() => setEditing(true)}
          >
            <Pencil className="h-3.5 w-3.5" />
          </Button>
          <Button
            size="icon"
            variant="ghost"
            className="h-7 w-7 text-destructive hover:text-destructive"
            onClick={() => {
              if (confirm(`Delete state "${state.name}"?`)) deleteState(state.id)
            }}
            disabled={isDeleting}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      )}
    </div>
  )
}

// ── Add state form ─────────────────────────────────────────────────────────
interface AddStateFormProps {
  orgId: string
  projectId: string
  nextPosition: number
  onDone: () => void
}

function AddStateForm({ orgId, projectId, nextPosition, onDone }: AddStateFormProps) {
  const [name, setName] = useState("")
  const [color, setColor] = useState(PRESET_COLORS[0])
  const [group, setGroup] = useState<StateGroup>("unstarted")

  const { mutate: createState, isPending } = useCreateProjectState(orgId, projectId)

  function submit() {
    if (!name.trim()) return
    createState({ name: name.trim(), color, group, position: nextPosition }, { onSuccess: onDone })
  }

  return (
    <div className="flex items-center gap-2 p-2 rounded-lg border border-dashed bg-muted/20">
      <div className="flex gap-1 shrink-0">
        {PRESET_COLORS.map((c) => (
          <button
            key={c}
            type="button"
            className="w-5 h-5 rounded-full border-2 transition-all"
            style={{
              backgroundColor: c,
              borderColor: color === c ? "white" : c,
              outline: color === c ? `2px solid ${c}` : "none",
            }}
            onClick={() => setColor(c)}
          />
        ))}
      </div>
      <Input
        className="h-7 text-sm flex-1"
        placeholder="State name…"
        value={name}
        onChange={(e) => setName(e.target.value)}
        onKeyDown={(e) => { if (e.key === "Enter") submit(); if (e.key === "Escape") onDone() }}
        autoFocus
      />
      <Select value={group} onValueChange={(v) => setGroup(v as StateGroup)}>
        <SelectTrigger className="h-7 w-32 text-xs">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {STATE_GROUPS.map((g) => (
            <SelectItem key={g} value={g} className="text-xs">
              {STATE_GROUP_LABELS[g]}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Button size="sm" className="h-7 text-xs" onClick={submit} disabled={isPending || !name.trim()}>
        Add
      </Button>
      <Button size="icon" variant="ghost" className="h-7 w-7" onClick={onDone}>
        <X className="h-3.5 w-3.5" />
      </Button>
    </div>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────
export function ProjectSettingsPage() {
  const { orgId = "", projectId = "" } = useParams<{ orgId: string; projectId: string }>()
  const navigate = useNavigate()
  const { data: project, isLoading } = useProject(orgId, projectId)
  const { mutate: updateProject, isPending: isUpdating } = useUpdateProject(orgId, projectId)
  const { mutate: deleteProject, isPending: isDeleting } = useDeleteProject(orgId, projectId)
  const { data: states = [] } = useProjectStates(orgId, projectId)
  const membership = useAppStore((s) => s.activeMembership)
  const [addingState, setAddingState] = useState(false)

  const canEdit = hasRole(membership?.role, "admin")

  const form = useForm<UpdateProjectValues>({
    resolver: zodResolver(updateProjectSchema),
    defaultValues: { name: "", description: "", status: "active" },
  })

  useEffect(() => {
    if (project) {
      form.reset({
        name: project.name,
        description: project.description ?? "",
        status: project.status,
      })
    }
  }, [project, form])

  function onSubmit(values: UpdateProjectValues) {
    updateProject({
      name: values.name,
      description: values.description || null,
      status: values.status,
    })
  }

  function handleDelete() {
    if (!confirm(`Delete project "${project?.name}"? This cannot be undone.`)) return
    deleteProject(undefined)
  }

  if (isLoading) {
    return (
      <div className="max-w-2xl mx-auto space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (!project) {
    return (
      <div className="max-w-2xl mx-auto text-center py-20">
        <p className="text-muted-foreground">Project not found.</p>
        <Button variant="link" onClick={() => navigate(`/orgs/${orgId}/projects`)}>
          Back to projects
        </Button>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate(`/orgs/${orgId}/projects`)}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex items-center gap-2">
          <h1 className="text-2xl font-semibold">{project.name}</h1>
          <ProjectStatusBadge status={project.status} />
        </div>
      </div>

      {/* Settings Form */}
      <Card>
        <CardHeader>
          <CardTitle>Project Settings</CardTitle>
          <CardDescription>Update your project details and status.</CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Name</FormLabel>
                    <FormControl>
                      <Input placeholder="Project name" disabled={!canEdit} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Description <span className="text-muted-foreground">(optional)</span></FormLabel>
                    <FormControl>
                      <Input
                        placeholder="What is this project about?"
                        disabled={!canEdit}
                        {...field}
                        value={field.value ?? ""}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="status"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Status</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value}
                      disabled={!canEdit}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="active">Active</SelectItem>
                        <SelectItem value="archived">Archived</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {canEdit && (
                <div className="flex justify-end pt-2">
                  <Button type="submit" disabled={isUpdating}>
                    {isUpdating ? "Saving…" : "Save changes"}
                  </Button>
                </div>
              )}
            </form>
          </Form>
        </CardContent>
      </Card>

      {/* Workflow States */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Workflow States</CardTitle>
              <CardDescription>
                Customize the states tasks move through in this project.
              </CardDescription>
            </div>
            {canEdit && !addingState && (
              <Button size="sm" variant="outline" onClick={() => setAddingState(true)}>
                <Plus className="h-4 w-4 mr-1" />
                Add state
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-1.5">
          {states.map((state) => (
            <StateRow
              key={state.id}
              state={state}
              canEdit={canEdit}
              orgId={orgId}
              projectId={projectId}
            />
          ))}
          {states.length === 0 && !addingState && (
            <p className="text-sm text-muted-foreground py-4 text-center">
              No states yet. Add one to get started.
            </p>
          )}
          {addingState && (
            <AddStateForm
              orgId={orgId}
              projectId={projectId}
              nextPosition={states.length}
              onDone={() => setAddingState(false)}
            />
          )}
        </CardContent>
      </Card>

      {/* Danger Zone */}
      {canEdit && (
        <Card className="border-destructive/50">
          <CardHeader>
            <CardTitle className="text-destructive">Danger Zone</CardTitle>
            <CardDescription>
              Permanently delete this project. This action cannot be undone.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={isDeleting}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              {isDeleting ? "Deleting…" : "Delete project"}
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
