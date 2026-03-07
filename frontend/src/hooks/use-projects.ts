import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"
import { toast } from "sonner"
import { apiClient } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"
import type { Project } from "@/types/project"
import type { CreateProjectValues, UpdateProjectValues } from "@/validations/project.schema"

export function useProjects(orgId: string) {
  return useQuery({
    queryKey: queryKeys.projects(orgId),
    queryFn: () =>
      apiClient.get(`organizations/${orgId}/projects`).json<Project[]>(),
    enabled: !!orgId,
    staleTime: 1000 * 60,
  })
}

export function useProject(orgId: string, projectId: string) {
  return useQuery({
    queryKey: queryKeys.project(orgId, projectId),
    queryFn: () =>
      apiClient.get(`organizations/${orgId}/projects/${projectId}`).json<Project>(),
    enabled: !!orgId && !!projectId,
    staleTime: 1000 * 60,
  })
}

export function useCreateProject(orgId: string) {
  const qc = useQueryClient()
  const navigate = useNavigate()

  return useMutation({
    mutationFn: (data: CreateProjectValues) =>
      apiClient
        .post(`organizations/${orgId}/projects`, { json: data })
        .json<Project>(),
    onSuccess: (project) => {
      qc.invalidateQueries({ queryKey: queryKeys.projects(orgId) })
      toast.success(`Project "${project.name}" created`)
      navigate(`/orgs/${orgId}/projects/${project.id}`)
    },
    onError: async (err: unknown) => {
      toast.error((await extractDetail(err)) ?? "Failed to create project")
    },
  })
}

export function useUpdateProject(orgId: string, projectId: string) {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (data: UpdateProjectValues) =>
      apiClient
        .patch(`organizations/${orgId}/projects/${projectId}`, { json: data })
        .json<Project>(),
    onSuccess: (project) => {
      qc.setQueryData(queryKeys.project(orgId, projectId), project)
      qc.invalidateQueries({ queryKey: queryKeys.projects(orgId) })
      toast.success("Project updated")
    },
    onError: async (err: unknown) => {
      toast.error((await extractDetail(err)) ?? "Failed to update project")
    },
  })
}

export function useDeleteProject(orgId: string, projectId: string) {
  const qc = useQueryClient()
  const navigate = useNavigate()

  return useMutation({
    mutationFn: () =>
      apiClient
        .delete(`organizations/${orgId}/projects/${projectId}`)
        .then(() => undefined),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.projects(orgId) })
      toast.success("Project deleted")
      navigate(`/orgs/${orgId}/projects`)
    },
    onError: async (err: unknown) => {
      toast.error((await extractDetail(err)) ?? "Failed to delete project")
    },
  })
}

async function extractDetail(err: unknown): Promise<string | null> {
  if (err && typeof err === "object" && "response" in err) {
    try {
      const body = await (err as { response: Response }).response.json() as {
        detail?: string
      }
      return body.detail ?? null
    } catch {
      return null
    }
  }
  return null
}
