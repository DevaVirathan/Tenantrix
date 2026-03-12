import { useInfiniteQuery, useQuery } from "@tanstack/react-query"
import { apiClient } from "@/lib/api-client"
import { queryKeys } from "@/lib/query-keys"
import type { AuditLog, AuditFilters } from "@/types/audit"

const PAGE_SIZE = 50

export function useAuditLogs(orgId: string, filters: Omit<AuditFilters, "limit" | "offset"> = {}) {
  return useInfiniteQuery({
    queryKey: queryKeys.auditLogs(orgId, filters as Record<string, unknown>),
    queryFn: async ({ pageParam = 0 }) => {
      const searchParams: Record<string, string> = {
        limit: String(PAGE_SIZE),
        offset: String(pageParam),
      }
      if (filters.action) searchParams.action = filters.action
      if (filters.resource_type) searchParams.resource_type = filters.resource_type
      if (filters.actor_user_id) searchParams.actor_user_id = filters.actor_user_id
      if (filters.since) searchParams.since = filters.since
      if (filters.until) searchParams.until = filters.until

      return apiClient
        .get(`organizations/${orgId}/audit-logs`, { searchParams })
        .json<AuditLog[]>()
    },
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) => {
      if (lastPage.length < PAGE_SIZE) return undefined
      return allPages.flat().length
    },
    enabled: !!orgId,
    staleTime: 1000 * 30,
  })
}

/** Fetch all audit events for a single task — accessible by any member. */
export function useTaskActivity(orgId: string, taskId: string) {
  return useQuery({
    queryKey: queryKeys.taskActivity(orgId, taskId),
    queryFn: () =>
      apiClient
        .get(`organizations/${orgId}/tasks/${taskId}/activity`, {
          searchParams: { limit: "100", offset: "0" },
        })
        .json<AuditLog[]>(),
    enabled: !!orgId && !!taskId,
    staleTime: 0,
  })
}
