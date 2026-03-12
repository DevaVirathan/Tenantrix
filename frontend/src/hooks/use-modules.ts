import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { apiClient } from "@/lib/api-client"
import type { Module } from "@/types/module"

async function extractDetail(err: unknown): Promise<string | null> {
  if (err && typeof err === "object" && "response" in err) {
    try {
      const body = await (err as { response: Response }).response.json() as { detail?: string }
      return body.detail ?? null
    } catch { return null }
  }
  return null
}

export function useModules(orgId: string, projectId: string) {
  return useQuery({
    queryKey: ["org", orgId, "project", projectId, "modules"],
    queryFn: () =>
      apiClient.get(`organizations/${orgId}/projects/${projectId}/modules`).json<Module[]>(),
    enabled: !!orgId && !!projectId,
    staleTime: 1000 * 30,
  })
}

export function useCreateModule(orgId: string, projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { name: string; description?: string | null; start_date?: string | null; end_date?: string | null }) =>
      apiClient.post(`organizations/${orgId}/projects/${projectId}/modules`, { json: data }).json<Module>(),
    onSuccess: (mod) => {
      qc.invalidateQueries({ queryKey: ["org", orgId, "project", projectId, "modules"] })
      toast.success(`Module "${mod.name}" created`)
    },
    onError: async (err: unknown) => {
      toast.error((await extractDetail(err)) ?? "Failed to create module")
    },
  })
}

export function useUpdateModule(orgId: string, projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ moduleId, data }: { moduleId: string; data: Record<string, unknown> }) =>
      apiClient.patch(`organizations/${orgId}/modules/${moduleId}`, { json: data }).json<Module>(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["org", orgId, "project", projectId, "modules"] })
    },
    onError: async (err: unknown) => {
      toast.error((await extractDetail(err)) ?? "Failed to update module")
    },
  })
}

export function useDeleteModule(orgId: string, projectId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (moduleId: string) =>
      apiClient.delete(`organizations/${orgId}/modules/${moduleId}`).then(() => undefined),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["org", orgId, "project", projectId, "modules"] })
      toast.success("Module deleted")
    },
    onError: async (err: unknown) => {
      toast.error((await extractDetail(err)) ?? "Failed to delete module")
    },
  })
}
