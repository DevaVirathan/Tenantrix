import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { apiClient } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"
import type { Invite } from "@/types/org"
import type { CreateInviteValues } from "@/validations/org.schema"

export function useInvites(orgId: string) {
  return useQuery({
    queryKey: queryKeys.invites(orgId),
    queryFn: () => apiClient.get(`organizations/${orgId}/invites`).json<Invite[]>(),
    enabled: !!orgId,
    staleTime: 1000 * 30,
  })
}

export function useCreateInvite(orgId: string) {
  const qc = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateInviteValues) =>
      apiClient.post(`organizations/${orgId}/invites`, { json: data }).json<Invite>(),
    onSuccess: (invite) => {
      qc.invalidateQueries({ queryKey: queryKeys.invites(orgId) })
      toast.success(`Invite sent to ${invite.email}`)
    },
    onError: async (err: unknown) => {
      const msg = await extractDetail(err) ?? "Failed to send invite"
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
