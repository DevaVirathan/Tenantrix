import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { apiClient } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"

export interface Watcher {
  user_id: string
  full_name: string | null
  email: string
}

export function useWatchers(orgId: string, taskId: string) {
  return useQuery({
    queryKey: queryKeys.watchers(orgId, taskId),
    queryFn: () =>
      apiClient.get(`organizations/${orgId}/tasks/${taskId}/watchers`).json<Watcher[]>(),
    enabled: !!orgId && !!taskId,
  })
}

export function useToggleWatch(orgId: string, taskId: string) {
  const qc = useQueryClient()
  const key = queryKeys.watchers(orgId, taskId)

  const watch = useMutation({
    mutationFn: () =>
      apiClient.post(`organizations/${orgId}/tasks/${taskId}/watchers`).json(),
    onSuccess: () => qc.invalidateQueries({ queryKey: key }),
  })

  const unwatch = useMutation({
    mutationFn: () =>
      apiClient.delete(`organizations/${orgId}/tasks/${taskId}/watchers`),
    onSuccess: () => qc.invalidateQueries({ queryKey: key }),
  })

  return { watch, unwatch }
}
