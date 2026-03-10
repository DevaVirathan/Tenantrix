import { useMutation, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { apiClient } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"
import type { TaskLinkOut, LinkType } from "@/types/task"

async function extractDetail(err: unknown): Promise<string | null> {
  if (err && typeof err === "object" && "response" in err) {
    try {
      const body = await (err as { response: Response }).response.json() as { detail?: string }
      return body.detail ?? null
    } catch { return null }
  }
  return null
}

export function useCreateTaskLink(orgId: string, projectId: string, taskId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { target_task_id: string; link_type: LinkType }) =>
      apiClient
        .post(`organizations/${orgId}/tasks/${taskId}/links`, { json: data })
        .json<TaskLinkOut>(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.task(orgId, taskId) })
      qc.invalidateQueries({ queryKey: queryKeys.tasks(orgId, projectId) })
      toast.success("Link created")
    },
    onError: async (err: unknown) => {
      toast.error((await extractDetail(err)) ?? "Failed to create link")
    },
  })
}

export function useDeleteTaskLink(orgId: string, projectId: string, taskId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (linkId: string) =>
      apiClient
        .delete(`organizations/${orgId}/tasks/links/${linkId}`)
        .then(() => undefined),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.task(orgId, taskId) })
      qc.invalidateQueries({ queryKey: queryKeys.tasks(orgId, projectId) })
      toast.success("Link removed")
    },
    onError: async (err: unknown) => {
      toast.error((await extractDetail(err)) ?? "Failed to remove link")
    },
  })
}
