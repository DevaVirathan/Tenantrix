import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { apiClient } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"
import type { ProjectState } from "@/types/project-state"

export function useProjectStates(orgId: string, projectId: string) {
  return useQuery({
    queryKey: queryKeys.projectStates(orgId, projectId),
    queryFn: () =>
      apiClient
        .get(`organizations/${orgId}/projects/${projectId}/states`)
        .json<ProjectState[]>(),
    enabled: !!orgId && !!projectId,
    staleTime: 1000 * 60,
  })
}

export function useCreateProjectState(orgId: string, projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { name: string; color: string; group: string; position: number; is_default?: boolean }) =>
      apiClient
        .post(`organizations/${orgId}/projects/${projectId}/states`, { json: data })
        .json<ProjectState>(),
    onSuccess: (state) => {
      qc.invalidateQueries({ queryKey: queryKeys.projectStates(orgId, projectId) })
      toast.success(`State "${state.name}" created`)
    },
    onError: () => toast.error("Failed to create state"),
  })
}

export function useUpdateProjectState(orgId: string, projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ stateId, data }: { stateId: string; data: Record<string, unknown> }) =>
      apiClient
        .patch(`organizations/${orgId}/states/${stateId}`, { json: data })
        .json<ProjectState>(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.projectStates(orgId, projectId) })
    },
    onError: () => toast.error("Failed to update state"),
  })
}

export function useDeleteProjectState(orgId: string, projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (stateId: string) =>
      apiClient.delete(`organizations/${orgId}/states/${stateId}`).then(() => undefined),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.projectStates(orgId, projectId) })
      toast.success("State deleted")
    },
    onError: () => toast.error("Failed to delete state"),
  })
}

export function useReorderProjectStates(orgId: string, projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (stateIds: string[]) =>
      apiClient
        .patch(`organizations/${orgId}/projects/${projectId}/states/reorder`, {
          json: { state_ids: stateIds },
        })
        .json<ProjectState[]>(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.projectStates(orgId, projectId) })
    },
    onError: () => toast.error("Failed to reorder states"),
  })
}
