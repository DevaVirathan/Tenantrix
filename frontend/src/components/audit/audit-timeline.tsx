import {
  CheckSquare,
  Users,
  FolderKanban,
  Building2,
  Mail,
  MessageSquare,
  Activity,
} from "lucide-react"
import { cn } from "@/lib/utils"
import type { AuditLog } from "@/types/audit"

// Map action prefix → icon component
function actionIcon(action: string): React.ComponentType<{ className?: string }> {
  if (action.startsWith("task.")) return CheckSquare
  if (action.startsWith("member.")) return Users
  if (action.startsWith("project.")) return FolderKanban
  if (action.startsWith("org.")) return Building2
  if (action.startsWith("invite.")) return Mail
  if (action.startsWith("comment.")) return MessageSquare
  return Activity
}

// Map action prefix → accent colour (Tailwind bg utility classes)
function actionColor(action: string): string {
  if (action.startsWith("task.")) return "bg-blue-500"
  if (action.startsWith("member.")) return "bg-purple-500"
  if (action.startsWith("project.")) return "bg-green-500"
  if (action.startsWith("org.")) return "bg-orange-500"
  if (action.startsWith("invite.")) return "bg-teal-500"
  if (action.startsWith("comment.")) return "bg-pink-500"
  return "bg-gray-500"
}

// Build a human-readable sentence from an audit log entry
function actionToSentence(log: AuditLog): string {
  const meta = log.metadata ?? {}
  const res = log.resource_id ? ` (${log.resource_id})` : ""

  switch (log.action) {
    case "org.created":
      return `Organisation created`
    case "org.updated":
      return `Organisation settings updated`
    case "invite.sent":
      return `Invite sent to ${String(meta.email ?? "someone")}`
    case "invite.accepted":
      return `Invite accepted`
    case "member.role_changed":
      return `Member role changed to ${String(meta.new_role ?? "unknown")}`
    case "member.removed":
      return `Member removed from organisation`
    case "project.created":
      return `Project "${String(meta.name ?? log.resource_id ?? "")}" created`
    case "project.updated":
      return `Project updated`
    case "project.deleted":
      return `Project deleted${res}`
    case "task.created":
      return `Task "${String(meta.title ?? log.resource_id ?? "")}" created`
    case "task.updated":
      return `Task updated${res}`
    case "task.deleted":
      return `Task deleted${res}`
    case "task.label_added":
      return `Label "${String(meta.label ?? "")}" added to task${res}`
    case "task.label_removed":
      return `Label "${String(meta.label ?? "")}" removed from task${res}`
    case "comment.created":
      return `Comment posted on task${res}`
    case "comment.updated":
      return `Comment edited on task${res}`
    case "comment.deleted":
      return `Comment deleted on task${res}`
    default:
      return log.action
  }
}

function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60_000)
  if (mins < 1) return "just now"
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  if (days < 30) return `${days}d ago`
  return new Date(iso).toLocaleString()
}

interface AuditTimelineProps {
  logs: AuditLog[]
  actorNames: Record<string, string>
}

export function AuditTimeline({ logs, actorNames }: AuditTimelineProps) {
  return (
    <ol className="relative">
      {logs.map((log, idx) => {
        const Icon = actionIcon(log.action)
        const color = actionColor(log.action)
        const isLast = idx === logs.length - 1
        const actorName = log.actor_user_id
          ? (actorNames[log.actor_user_id] ?? "Unknown user")
          : "System"

        return (
          <li key={log.id} className="flex gap-3">
            {/* Timeline spine + icon */}
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  "flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-white",
                  color
                )}
              >
                <Icon className="h-3.5 w-3.5" />
              </div>
              {!isLast && <div className="w-px flex-1 bg-border mt-1 mb-1" />}
            </div>

            {/* Content */}
            <div className={cn("pb-4 flex-1 min-w-0", isLast && "pb-0")}>
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm leading-snug">
                  <span className="font-medium text-foreground">{actorName}</span>{" "}
                  <span className="text-muted-foreground">{actionToSentence(log)}</span>
                </p>
                <time
                  className="shrink-0 text-xs text-muted-foreground mt-0.5 whitespace-nowrap"
                  title={new Date(log.created_at).toLocaleString()}
                >
                  {relativeTime(log.created_at)}
                </time>
              </div>

              {/* Resource type / ID badge */}
              {(log.resource_type || log.resource_id) && (
                <p className="mt-0.5 text-xs text-muted-foreground/70">
                  {log.resource_type && (
                    <span className="font-mono bg-muted rounded px-1 py-0.5 mr-1">
                      {log.resource_type}
                    </span>
                  )}
                  {log.resource_id && (
                    <span className="font-mono text-muted-foreground/50">
                      {log.resource_id}
                    </span>
                  )}
                </p>
              )}
            </div>
          </li>
        )
      })}
    </ol>
  )
}
