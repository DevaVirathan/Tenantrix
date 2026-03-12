import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { apiClient } from "@/lib/api-client"
import type { SavedView, SavedViewCreate } from "@/types/saved-view"

export function useSavedViews(orgId: string, projectId: string) {
  return useQuery({
    queryKey: ["org", orgId, "project", projectId, "views"],
    queryFn: () =>
      apiClient
        .get(`organizations/${orgId}/projects/${projectId}/views`)
        .json<SavedView[]>(),
    enabled: !!orgId && !!projectId,
  })
}

export function useCreateSavedView(orgId: string, projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: SavedViewCreate) =>
      apiClient
        .post(`organizations/${orgId}/projects/${projectId}/views`, { json: data })
        .json<SavedView>(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["org", orgId, "project", projectId, "views"] })
      toast.success("View saved")
    },
    onError: () => {
      toast.error("Failed to save view")
    },
  })
}

export function useDeleteSavedView(orgId: string, projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (viewId: string) =>
      apiClient.delete(`organizations/${orgId}/views/${viewId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["org", orgId, "project", projectId, "views"] })
      toast.success("View deleted")
    },
    onError: () => {
      toast.error("Failed to delete view")
    },
  })
}
