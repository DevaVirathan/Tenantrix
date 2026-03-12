import { useEffect, useRef, useCallback } from "react"
import { useQueryClient } from "@tanstack/react-query"
import { useAppStore } from "@/store/app-store"

interface WSEvent {
  type: string
  payload: Record<string, unknown>
}

export function useWebSocket(orgId: string | undefined) {
  const qc = useQueryClient()
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>(undefined)
  const accessToken = useAppStore((s) => s.accessToken)

  const connect = useCallback(() => {
    if (!orgId || !accessToken) return

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:"
    const host = window.location.host
    const url = `${protocol}//${host}/api/v1/ws/${orgId}?token=${accessToken}`

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      console.debug("[WS] connected")
    }

    ws.onmessage = (e) => {
      try {
        const event: WSEvent = JSON.parse(e.data)
        handleEvent(event)
      } catch {
        // ignore invalid messages
      }
    }

    ws.onclose = () => {
      console.debug("[WS] disconnected, reconnecting in 3s")
      reconnectTimer.current = setTimeout(connect, 3000)
    }

    ws.onerror = () => {
      ws.close()
    }
  }, [orgId, accessToken])

  function handleEvent(event: WSEvent) {
    const { type, payload } = event
    const projectId = payload.project_id as string | undefined

    switch (type) {
      case "task_created":
      case "task_updated":
      case "task_deleted":
        if (projectId) {
          qc.invalidateQueries({ queryKey: ["org", orgId, "project", projectId, "tasks"] })
          qc.invalidateQueries({ queryKey: ["org", orgId, "project", projectId, "sprints"] })
        }
        if (payload.id) {
          qc.invalidateQueries({ queryKey: ["org", orgId, "task", payload.id] })
        }
        break
      case "comment_added":
        if (payload.task_id) {
          qc.invalidateQueries({ queryKey: ["org", orgId, "task", payload.task_id, "comments"] })
        }
        break
      case "sprint_updated":
        if (projectId) {
          qc.invalidateQueries({ queryKey: ["org", orgId, "project", projectId, "sprints"] })
        }
        break
      case "notification_new":
        qc.invalidateQueries({ queryKey: ["notifications"] })
        break
    }
  }

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [connect])
}
