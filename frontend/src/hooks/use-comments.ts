import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { apiClient } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"
import type { Comment } from "@/types/comment"
import type { CreateCommentValues, UpdateCommentValues } from "@/validations/comment.schema"

async function extractDetail(err: unknown): Promise<string | null> {
  if (err && typeof err === "object" && "response" in err) {
    try {
      const body = await (err as { response: Response }).response.json() as { detail?: string }
      return body.detail ?? null
    } catch { return null }
  }
  return null
}

export function useComments(orgId: string, taskId: string) {
  return useQuery({
    queryKey: queryKeys.comments(orgId, taskId),
    queryFn: () =>
      apiClient
        .get(`organizations/${orgId}/tasks/${taskId}/comments`)
        .json<Comment[]>(),
    enabled: !!orgId && !!taskId,
    staleTime: 1000 * 30,
  })
}

export function useCreateComment(orgId: string, taskId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateCommentValues) =>
      apiClient
        .post(`organizations/${orgId}/tasks/${taskId}/comments`, { json: data })
        .json<Comment>(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.comments(orgId, taskId) })
    },
    onError: async (err: unknown) => {
      toast.error((await extractDetail(err)) ?? "Failed to add comment")
    },
  })
}

export function useUpdateComment(orgId: string, taskId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ commentId, data }: { commentId: string; data: UpdateCommentValues }) =>
      apiClient
        .patch(`organizations/${orgId}/comments/${commentId}`, { json: data })
        .json<Comment>(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.comments(orgId, taskId) })
    },
    onError: async (err: unknown) => {
      toast.error((await extractDetail(err)) ?? "Failed to update comment")
    },
  })
}

export function useDeleteComment(orgId: string, taskId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (commentId: string) =>
      apiClient
        .delete(`organizations/${orgId}/comments/${commentId}`)
        .then(() => undefined),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.comments(orgId, taskId) })
    },
    onError: async (err: unknown) => {
      toast.error((await extractDetail(err)) ?? "Failed to delete comment")
    },
  })
}
