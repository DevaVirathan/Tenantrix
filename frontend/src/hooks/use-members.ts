import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { apiClient } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"
import type { Member, OrgRole } from "@/types/org"

export function useMembers(orgId: string) {
  return useQuery({
    queryKey: queryKeys.members(orgId),
    queryFn: () => apiClient.get(`organizations/${orgId}/members`).json<Member[]>(),
    enabled: !!orgId,
    staleTime: 1000 * 60,
  })
}

export function useUpdateMemberRole(orgId: string) {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: OrgRole }) =>
      apiClient
        .patch(`organizations/${orgId}/members/${userId}/role`, { json: { role } })
        .json<Member>(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.members(orgId) })
      toast.success("Role updated")
    },
    onError: async (err: unknown) => {
      const msg = await extractDetail(err) ?? "Failed to update role"
      toast.error(msg)
    },
  })
}

export function useRemoveMember(orgId: string) {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (userId: string) =>
      apiClient.delete(`organizations/${orgId}/members/${userId}`).then(() => undefined),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.members(orgId) })
      toast.success("Member removed")
    },
    onError: async (err: unknown) => {
      const msg = await extractDetail(err) ?? "Failed to remove member"
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
