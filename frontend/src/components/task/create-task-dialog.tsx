import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import {
  Dialog, DialogContent, DialogDescription, DialogFooter,
  DialogHeader, DialogTitle, DialogTrigger,
} from "@/components/ui/dialog"
import {
  Form, FormControl, FormField, FormItem, FormLabel, FormMessage,
} from "@/components/ui/form"
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { AssigneePicker } from "./assignee-picker"
import { PriorityIcon } from "./priority-icon"
import { RichTextEditor } from "@/components/shared/rich-text-editor"
import { DatePicker } from "@/components/shared/date-picker"
import { createTaskSchema, type CreateTaskValues } from "@/validations/task.schema"
import { useCreateTask } from "@/hooks/use-tasks"
import { useProjectStates } from "@/hooks/use-project-states"
import { useAppStore } from "@/store/app-store"
import type { IssueType } from "@/types/task"
import { TASK_PRIORITY_LABELS, ISSUE_TYPE_LABELS } from "@/types/task"
import { IssueTypeIcon } from "./issue-type-icon"

interface CreateTaskDialogProps {
  orgId: string
  projectId: string
  defaultStateId?: string
  children: React.ReactNode
}

export function CreateTaskDialog({ orgId, projectId, defaultStateId, children }: CreateTaskDialogProps) {
  const storeOpen = useAppStore((s) => s.createDialogOpen)
  const setStoreOpen = useAppStore((s) => s.setCreateDialogOpen)
  const [localOpen, setLocalOpen] = useState(false)
  const open = localOpen || storeOpen
  const setOpen = (v: boolean) => { setLocalOpen(v); setStoreOpen(v) }
  const { mutate: createTask, isPending } = useCreateTask(orgId, projectId)
  const { data: states = [] } = useProjectStates(orgId, projectId)

  // Find the default state: use provided defaultStateId, or project's default, or first state
  const resolvedDefaultStateId =
    defaultStateId ??
    states.find((s) => s.is_default)?.id ??
    states[0]?.id ??
    ""

  const form = useForm<CreateTaskValues>({
    resolver: zodResolver(createTaskSchema),
    defaultValues: {
      title: "",
      description: "",
      status: "todo",
      priority: "medium" as const,
      issue_type: "task" as const,
      assignee_user_id: null,
      state_id: resolvedDefaultStateId || null,
      position: 0,
      story_points: null,
      start_date: null,
      due_date: null,
    },
  })

  // Update state_id when dialog opens with a different default
  function handleOpenChange(isOpen: boolean) {
    setOpen(isOpen)
    if (isOpen && resolvedDefaultStateId) {
      form.setValue("state_id", resolvedDefaultStateId)
    }
    if (!isOpen) {
      form.reset()
    }
  }

  function onSubmit(values: CreateTaskValues) {
    createTask(
      { ...values, description: values.description || undefined },
      { onSuccess: () => { form.reset(); setOpen(false) } }
    )
  }

  const priorities = Object.keys(TASK_PRIORITY_LABELS) as (keyof typeof TASK_PRIORITY_LABELS)[]

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Create Task</DialogTitle>
          <DialogDescription>Add a new task to this project.</DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="title"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Title</FormLabel>
                  <FormControl><Input placeholder="Task title…" {...field} /></FormControl>
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
                    <RichTextEditor
                      content={field.value ?? ""}
                      onChange={field.onChange}
                      placeholder="Describe the task…"
                      minimal
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="grid grid-cols-2 gap-3">
              {/* State (dynamic) */}
              <FormField
                control={form.control}
                name="state_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>State</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value ?? ""}>
                      <FormControl>
                        <SelectTrigger><SelectValue placeholder="Select state" /></SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {states.map((s) => (
                          <SelectItem key={s.id} value={s.id}>
                            <span className="flex items-center gap-2">
                              <span
                                className="inline-block h-2 w-2 rounded-full shrink-0"
                                style={{ backgroundColor: s.color }}
                              />
                              {s.name}
                            </span>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="priority"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Priority</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
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
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <FormField
                control={form.control}
                name="issue_type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Type</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value ?? "task"}>
                      <FormControl>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                      </FormControl>
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
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="story_points"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Points <span className="text-muted-foreground">(optional)</span></FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={0}
                        max={100}
                        placeholder="—"
                        value={field.value ?? ""}
                        onChange={(e) => field.onChange(e.target.value === "" ? null : Number(e.target.value))}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <FormField
                control={form.control}
                name="start_date"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Start date <span className="text-muted-foreground">(optional)</span></FormLabel>
                    <FormControl>
                      <DatePicker
                        value={field.value ?? null}
                        onChange={field.onChange}
                        placeholder="Start date"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="due_date"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Due date <span className="text-muted-foreground">(optional)</span></FormLabel>
                    <FormControl>
                      <DatePicker
                        value={field.value ?? null}
                        onChange={field.onChange}
                        placeholder="Due date"
                      />
                    </FormControl>
                    <FormMessage />
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
                  />
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setOpen(false)} disabled={isPending}>
                Cancel
              </Button>
              <Button type="submit" disabled={isPending}>
                {isPending ? "Creating…" : "Create Task"}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
