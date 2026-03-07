import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"
import { toast } from "sonner"
import { apiClient } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"
import { useAppStore } from "@/store/app-store"
import type { Organization } from "@/types/org"
import type { CreateOrgValues, UpdateOrgValues } from "@/validations/org.schema"

export function useOrgs() {
  return useQuery({
    queryKey: queryKeys.orgs(),
    queryFn: () => apiClient.get("organizations").json<Organization[]>(),
    staleTime: 1000 * 60 * 2,
  })
}

export function useOrg(orgId: string) {
  return useQuery({
    queryKey: queryKeys.org(orgId),
    queryFn: () => apiClient.get(`organizations/${orgId}`).json<Organization>(),
    enabled: !!orgId,
    staleTime: 1000 * 60 * 2,
  })
}

export function useCreateOrg() {
  const qc = useQueryClient()
  const navigate = useNavigate()
  const setActiveOrg = useAppStore((s) => s.setActiveOrg)

  return useMutation({
    mutationFn: (data: CreateOrgValues) =>
      apiClient.post("organizations", { json: data }).json<Organization>(),
    onSuccess: (org) => {
      qc.invalidateQueries({ queryKey: queryKeys.orgs() })
      setActiveOrg(org, "owner")
      toast.success(`Organization "${org.name}" created`)
      navigate(`/orgs/${org.id}`)
    },
    onError: async (err: unknown) => {
      const msg = await extractDetail(err) ?? "Failed to create organization"
      toast.error(msg)
    },
  })
}

export function useUpdateOrg(orgId: string) {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (data: UpdateOrgValues) =>
      apiClient.patch(`organizations/${orgId}`, { json: data }).json<Organization>(),
    onSuccess: (org) => {
      qc.setQueryData(queryKeys.org(orgId), org)
      qc.invalidateQueries({ queryKey: queryKeys.orgs() })
      toast.success("Organization updated")
    },
    onError: async (err: unknown) => {
      const msg = await extractDetail(err) ?? "Failed to update organization"
      toast.error(msg)
    },
  })
}

export function useDeleteOrg(orgId: string) {
  const qc = useQueryClient()
  const navigate = useNavigate()
  const { activeOrg, logout } = useAppStore()

  return useMutation({
    mutationFn: () =>
      apiClient.delete(`organizations/${orgId}`).then(() => undefined),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.orgs() })
      toast.success("Organization deleted")
      if (activeOrg?.id === orgId) {
        logout()
        navigate("/login")
      } else {
        navigate("/orgs")
      }
    },
    onError: async (err: unknown) => {
      const msg = await extractDetail(err) ?? "Failed to delete organization"
      toast.error(msg)
    },
  })
}

async function extractDetail(err: unknown): Promise<string | null> {
  if (err && typeof err === "object" && "response" in err) {
    try {
      const body = await (err as { response: Response }).response.json() as { detail?: string }
      return body.detail ?? null
    } catch {
      return null
    }
  }
  return null
}
