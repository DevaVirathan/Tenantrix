import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { apiClient } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"
import type { Sprint, SprintStatus } from "@/types/sprint"

interface SprintCreateData {
  name: string
  description?: string | null
  start_date?: string | null
  end_date?: string | null
  goals?: string | null
}

interface SprintUpdateData {
  name?: string
  description?: string | null
  status?: SprintStatus
  start_date?: string | null
  end_date?: string | null
  goals?: string | null
}

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

export function useSprints(orgId: string, projectId: string, filters?: { status?: SprintStatus }) {
  const params: Record<string, string> = {}
  if (filters?.status) params.status = filters.status

  return useQuery({
    queryKey: queryKeys.sprints(orgId, projectId, filters as Record<string, unknown>),
    queryFn: () =>
      apiClient
        .get(`organizations/${orgId}/projects/${projectId}/sprints`, { searchParams: params })
        .json<Sprint[]>(),
    enabled: !!orgId && !!projectId,
    staleTime: 1000 * 30,
  })
}

export function useSprint(orgId: string, sprintId: string) {
  return useQuery({
    queryKey: queryKeys.sprint(orgId, sprintId),
    queryFn: () =>
      apiClient.get(`organizations/${orgId}/sprints/${sprintId}`).json<Sprint>(),
    enabled: !!orgId && !!sprintId,
    staleTime: 1000 * 30,
  })
}

// ── Mutations ─────────────────────────────────────────────────────────────────

export function useCreateSprint(orgId: string, projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: SprintCreateData) =>
      apiClient
        .post(`organizations/${orgId}/projects/${projectId}/sprints`, { json: data })
        .json<Sprint>(),
    onSuccess: (sprint) => {
      qc.invalidateQueries({ queryKey: queryKeys.sprints(orgId, projectId) })
      toast.success(`Sprint "${sprint.name}" created`)
    },
    onError: async (err: unknown) => {
      toast.error((await extractDetail(err)) ?? "Failed to create sprint")
    },
  })
}

export function useUpdateSprint(orgId: string, projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ sprintId, data }: { sprintId: string; data: SprintUpdateData }) =>
      apiClient
        .patch(`organizations/${orgId}/sprints/${sprintId}`, { json: data })
        .json<Sprint>(),
    onSuccess: (sprint) => {
      qc.setQueryData(queryKeys.sprint(orgId, sprint.id), sprint)
      qc.invalidateQueries({ queryKey: queryKeys.sprints(orgId, projectId) })
    },
    onError: async (err: unknown) => {
      toast.error((await extractDetail(err)) ?? "Failed to update sprint")
    },
  })
}

export function useDeleteSprint(orgId: string, projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (sprintId: string) =>
      apiClient.delete(`organizations/${orgId}/sprints/${sprintId}`).then(() => undefined),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.sprints(orgId, projectId) })
      toast.success("Sprint deleted")
    },
    onError: async (err: unknown) => {
      toast.error((await extractDetail(err)) ?? "Failed to delete sprint")
    },
  })
}
