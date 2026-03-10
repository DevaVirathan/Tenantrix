import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { apiClient } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"
import type { Task, TaskFilters } from "@/types/task"
import type { CreateTaskValues, UpdateTaskValues, CreateLabelValues } from "@/validations/task.schema"

async function extractDetail(err: unknown): Promise<string | null> {
  if (err && typeof err === "object" && "response" in err) {
    try {
      const body = await (err as { response: Response }).response.json() as { detail?: string }
      return body.detail ?? null
    } catch { return null }
  }
  return null
}

// ── Queries ──────────────────────────────────────────────────────────────────

export function useTasks(orgId: string, projectId: string, filters?: TaskFilters) {
  const params: Record<string, string> = {}
  if (filters?.status) params.status = filters.status
  if (filters?.priority) params.priority = filters.priority
  if (filters?.assignee_user_id) params.assignee_user_id = filters.assignee_user_id
  if (filters?.issue_type) params.issue_type = filters.issue_type
  if (filters?.sprint_id) params.sprint_id = filters.sprint_id
  if (filters?.no_sprint) params.no_sprint = "true"

  return useQuery({
    queryKey: queryKeys.tasks(orgId, projectId, filters as Record<string, unknown>),
    queryFn: () =>
      apiClient
        .get(`organizations/${orgId}/projects/${projectId}/tasks`, { searchParams: params })
        .json<Task[]>(),
    enabled: !!orgId && !!projectId,
    staleTime: 1000 * 30,
  })
}

export function useTask(orgId: string, taskId: string) {
  return useQuery({
    queryKey: queryKeys.task(orgId, taskId),
    queryFn: () =>
      apiClient.get(`organizations/${orgId}/tasks/${taskId}`).json<Task>(),
    enabled: !!orgId && !!taskId,
    staleTime: 1000 * 30,
  })
}

// ── Mutations ─────────────────────────────────────────────────────────────────

export function useCreateTask(orgId: string, projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateTaskValues) =>
      apiClient
        .post(`organizations/${orgId}/projects/${projectId}/tasks`, { json: data })
        .json<Task>(),
    onSuccess: (task) => {
      qc.invalidateQueries({ queryKey: ["org", orgId, "project", projectId, "tasks"] })
      toast.success(`Task "${task.title}" created`)
    },
    onError: async (err: unknown) => {
      toast.error((await extractDetail(err)) ?? "Failed to create task")
    },
  })
}

export function useUpdateTask(orgId: string, projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ taskId, data }: { taskId: string; data: UpdateTaskValues }) =>
      apiClient
        .patch(`organizations/${orgId}/tasks/${taskId}`, { json: data })
        .json<Task>(),
    onSuccess: (task) => {
      qc.setQueryData(queryKeys.task(orgId, task.id), task)
      qc.invalidateQueries({ queryKey: ["org", orgId, "project", projectId, "tasks"] })
      qc.invalidateQueries({ queryKey: queryKeys.taskActivity(orgId, task.id) })
    },
    onError: async (err: unknown) => {
      toast.error((await extractDetail(err)) ?? "Failed to update task")
      qc.invalidateQueries({ queryKey: ["org", orgId, "project", projectId, "tasks"] })
    },
  })
}

export function useDeleteTask(orgId: string, projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (taskId: string) =>
      apiClient.delete(`organizations/${orgId}/tasks/${taskId}`).then(() => undefined),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["org", orgId, "project", projectId, "tasks"] })
      toast.success("Task deleted")
    },
    onError: async (err: unknown) => {
      toast.error((await extractDetail(err)) ?? "Failed to delete task")
    },
  })
}

export function useAddLabel(orgId: string, projectId: string, taskId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateLabelValues) =>
      apiClient
        .post(`organizations/${orgId}/tasks/${taskId}/labels`, { json: data })
        .json<Task>(),
    onSuccess: (task) => {
      qc.setQueryData(queryKeys.task(orgId, taskId), task)
      qc.invalidateQueries({ queryKey: ["org", orgId, "project", projectId, "tasks"] })
    },
    onError: async (err: unknown) => {
      toast.error((await extractDetail(err)) ?? "Failed to add label")
    },
  })
}

export function useRemoveLabel(orgId: string, projectId: string, taskId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (labelName: string) =>
      apiClient
        .delete(`organizations/${orgId}/tasks/${taskId}/labels/${encodeURIComponent(labelName)}`)
        .then(() => undefined),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.task(orgId, taskId) })
      qc.invalidateQueries({ queryKey: ["org", orgId, "project", projectId, "tasks"] })
    },
    onError: async (err: unknown) => {
      toast.error((await extractDetail(err)) ?? "Failed to remove label")
    },
  })
}
