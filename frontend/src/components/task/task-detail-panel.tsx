import { useEffect } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { Trash2 } from "lucide-react"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import {
  Form, FormControl, FormField, FormItem, FormLabel,
} from "@/components/ui/form"
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Separator } from "@/components/ui/separator"
import { PriorityIcon } from "./priority-icon"
import { AssigneePicker } from "./assignee-picker"
import { LabelPicker } from "./label-picker"
import { useTask, useUpdateTask, useDeleteTask } from "@/hooks/use-tasks"
import { useAppStore } from "@/store/app-store"
import { hasRole } from "@/lib/rbac"
import { updateTaskSchema, type UpdateTaskValues } from "@/validations/task.schema"
import type { TaskStatus, TaskPriority } from "@/types/task"
import { TASK_STATUS_LABELS, TASK_PRIORITY_LABELS } from "@/types/task"

interface TaskDetailPanelProps {
  orgId: string
  projectId: string
}

export function TaskDetailPanel({ orgId, projectId }: TaskDetailPanelProps) {
  const taskPanelOpen = useAppStore((s) => s.taskPanelOpen)
  const activeTaskId = useAppStore((s) => s.activeTaskId)
  const closeTaskPanel = useAppStore((s) => s.closeTaskPanel)
  const membership = useAppStore((s) => s.activeMembership)

  const canEdit = hasRole(membership?.role, "member")
  const canDelete = hasRole(membership?.role, "admin")

  const { data: task, isLoading } = useTask(orgId, activeTaskId ?? "")
  const { mutate: updateTask, isPending: isUpdating } = useUpdateTask(orgId, projectId)
  const { mutate: deleteTask, isPending: isDeleting } = useDeleteTask(orgId, projectId)

  const form = useForm<UpdateTaskValues>({
    resolver: zodResolver(updateTaskSchema),
    defaultValues: { title: "", description: "", status: "todo", priority: "medium" },
  })

  useEffect(() => {
    if (task) {
      form.reset({
        title: task.title,
        description: task.description ?? "",
        status: task.status,
        priority: task.priority,
        assignee_user_id: task.assignee_user_id,
      })
    }
  }, [task, form])

  function onSubmit(values: UpdateTaskValues) {
    if (!task) return
    updateTask({ taskId: task.id, data: values })
  }

  function handleDelete() {
    if (!task) return
    if (!confirm(`Delete task "${task.title}"? This cannot be undone.`)) return
    deleteTask(task.id, { onSuccess: closeTaskPanel })
  }

  const statuses = Object.entries(TASK_STATUS_LABELS) as [TaskStatus, string][]
  const priorities = Object.keys(TASK_PRIORITY_LABELS) as TaskPriority[]

  return (
    <Sheet open={taskPanelOpen} onOpenChange={(o) => !o && closeTaskPanel()}>
      <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
        {isLoading || !task ? (
          <div className="space-y-4 pt-6">
            <Skeleton className="h-6 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-32 w-full" />
          </div>
        ) : (
          <>
            <SheetHeader className="pr-6">
              <SheetTitle className="text-left text-lg leading-snug line-clamp-2">
                {task.title}
              </SheetTitle>
              <SheetDescription className="text-left">
                Created {new Date(task.created_at).toLocaleDateString()}
              </SheetDescription>
            </SheetHeader>

            <Separator className="my-4" />

            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                <FormField
                  control={form.control}
                  name="title"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Title</FormLabel>
                      <FormControl>
                        <Input disabled={!canEdit} {...field} />
                      </FormControl>
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="description"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Description</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="Add a description…"
                          disabled={!canEdit}
                          {...field}
                          value={field.value ?? ""}
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />

                <div className="grid grid-cols-2 gap-3">
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
                            <SelectTrigger><SelectValue /></SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {statuses.map(([v, label]) => (
                              <SelectItem key={v} value={v}>{label}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="priority"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Priority</FormLabel>
                        <Select
                          onValueChange={field.onChange}
                          value={field.value}
                          disabled={!canEdit}
                        >
                          <FormControl>
                            <SelectTrigger><SelectValue /></SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {priorities.map((p) => (
                              <SelectItem key={p} value={p}>
                                <span className="flex items-center gap-2">
                                  <PriorityIcon priority={p} />
                                  {TASK_PRIORITY_LABELS[p]}
                                </span>
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </FormItem>
                    )}
                  />
                </div>

                <FormField
                  control={form.control}
                  name="assignee_user_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Assignee</FormLabel>
                      <AssigneePicker
                        orgId={orgId}
                        value={field.value ?? null}
                        onChange={field.onChange}
                        disabled={!canEdit}
                      />
                    </FormItem>
                  )}
                />

                {/* Labels */}
                <div>
                  <p className="text-sm font-medium mb-2">Labels</p>
                  <LabelPicker
                    orgId={orgId}
                    projectId={projectId}
                    taskId={task.id}
                    currentLabels={task.labels}
                    disabled={!canEdit}
                  />
                </div>

                {canEdit && (
                  <Button type="submit" className="w-full" disabled={isUpdating}>
                    {isUpdating ? "Saving…" : "Save changes"}
                  </Button>
                )}
              </form>
            </Form>

            {canDelete && (
              <>
                <Separator className="my-4" />
                <Button
                  variant="destructive"
                  size="sm"
                  className="gap-2"
                  onClick={handleDelete}
                  disabled={isDeleting}
                >
                  <Trash2 className="h-4 w-4" />
                  {isDeleting ? "Deleting…" : "Delete task"}
                </Button>
              </>
            )}
          </>
        )}
      </SheetContent>
    </Sheet>
  )
}
