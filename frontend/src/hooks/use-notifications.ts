import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { apiClient } from "@/lib/api-client"
import type { Notification } from "@/types/notification"

const KEYS = {
  notifications: (orgId?: string) => ["notifications", orgId] as const,
  unreadCount: () => ["notifications", "unread-count"] as const,
}

export function useNotifications(orgId?: string) {
  const params: Record<string, string> = {}
  if (orgId) params.org_id = orgId

  return useQuery({
    queryKey: KEYS.notifications(orgId),
    queryFn: () =>
      apiClient.get("notifications", { searchParams: params }).json<Notification[]>(),
    staleTime: 1000 * 15,
    refetchInterval: 1000 * 30,
  })
}

export function useUnreadCount() {
  return useQuery({
    queryKey: KEYS.unreadCount(),
    queryFn: () =>
      apiClient.get("notifications/unread-count").json<{ count: number }>(),
    staleTime: 1000 * 10,
    refetchInterval: 1000 * 20,
  })
}

export function useMarkAsRead() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (notificationId: string) =>
      apiClient.patch(`notifications/${notificationId}/read`).json<Notification>(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] })
    },
  })
}

export function useMarkAllRead() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () =>
      apiClient.post("notifications/mark-all-read").then(() => undefined),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] })
    },
  })
}
