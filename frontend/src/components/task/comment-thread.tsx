import { useEffect, useRef } from "react"
import { Skeleton } from "@/components/ui/skeleton"
import { Separator } from "@/components/ui/separator"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { CommentCard } from "./comment-card"
import { CommentForm } from "./comment-form"
import { useComments } from "@/hooks/use-comments"
import { useMembers } from "@/hooks/use-members"
import { useTaskActivity } from "@/hooks/use-audit-logs"
import { useAppStore } from "@/store/app-store"
import { hasRole } from "@/lib/rbac"
import type { AuditLog } from "@/types/audit"
import type { Comment } from "@/types/comment"
import { cn } from "@/lib/utils"

interface CommentThreadProps {
  orgId: string
  taskId: string
}

// ── Helpers ────────────────────────────────────────────────────────────────────

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

function initials(name: string) {
  return name.split(" ").map((w) => w[0]).join("").toUpperCase().slice(0, 2)
}

const AVATAR_COLORS = [
  "bg-blue-500", "bg-green-500", "bg-purple-500",
  "bg-orange-500", "bg-pink-500", "bg-teal-500",
]
function avatarColor(name: string) {
  let hash = 0
  for (const c of name) hash = (hash * 31 + c.charCodeAt(0)) % AVATAR_COLORS.length
  return AVATAR_COLORS[hash]
}

/** Convert an audit action string into a human-readable sentence (short form for activity feed) */
function activitySentence(log: AuditLog): string {
  const meta = log.metadata ?? {}
  switch (log.action) {
    case "task.created":    return "created the work item."
    case "task.updated":    return "updated the work item."
    case "task.deleted":    return "deleted the work item."
    case "task.label_added":
      return `added a new label ${String(meta.label ?? "")}.`
    case "task.label_removed":
      return `removed the label ${String(meta.label ?? "")}.`
    case "member.role_changed":
      return `changed role to ${String(meta.new_role ?? "unknown")}.`
    default: {
      // Generic: turn "task.status_updated" → "updated status to In Progress."
      const [, verb] = log.action.split(".")
      const field = String(meta.field ?? "")
      const newVal = String(meta.new_value ?? meta.to ?? "")
      if (field && newVal) return `set the ${field} to ${newVal}.`
      if (newVal) return `updated ${verb ?? log.action} to ${newVal}.`
      return `${(verb ?? log.action).replace(/_/g, " ")}.`
    }
  }
}

// ── Unified activity item type ─────────────────────────────────────────────────
type ActivityItem =
  | { kind: "event"; log: AuditLog; ts: number }
  | { kind: "comment"; comment: Comment; ts: number }

// ── Component ─────────────────────────────────────────────────────────────────

export function CommentThread({ orgId, taskId }: CommentThreadProps) {
  const membership = useAppStore((s) => s.activeMembership)
  const isAdmin = hasRole(membership?.role, "admin")

  const { data: comments = [], isLoading: commentsLoading } = useComments(orgId, taskId)
  const { data: members = [] } = useMembers(orgId)
  const { data: activityLogs = [], isLoading: logsLoading } = useTaskActivity(orgId, taskId, isAdmin)

  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [comments.length])

  function resolveName(userId: string | null): string {
    if (!userId) return "Deleted user"
    const member = members.find((m) => m.user_id === userId)
    return member?.full_name ?? member?.email ?? "Unknown"
  }

  // Merge & sort oldest-first (like Plane's Activity feed)
  const items: ActivityItem[] = [
    ...activityLogs.map((log): ActivityItem => ({
      kind: "event", log, ts: new Date(log.created_at).getTime(),
    })),
    ...comments.map((comment): ActivityItem => ({
      kind: "comment", comment, ts: new Date(comment.created_at).getTime(),
    })),
  ].sort((a, b) => a.ts - b.ts)

  const isLoading = commentsLoading || logsLoading

  return (
    <div className="flex flex-col gap-4">

      {/* Section heading */}
      <p className="text-sm font-semibold">Activity</p>

      {/* Feed */}
      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex gap-3">
              <Skeleton className="h-6 w-6 rounded-full shrink-0" />
              <div className="flex-1 space-y-1.5 pt-0.5">
                <Skeleton className="h-3.5 w-2/3" />
              </div>
            </div>
          ))}
        </div>
      ) : items.length === 0 ? (
        <p className="text-xs text-muted-foreground py-2">No activity yet.</p>
      ) : (
        <div className="flex flex-col gap-0">
          {items.map((item, idx) => {
            const isLast = idx === items.length - 1

            if (item.kind === "event") {
              const actorName = resolveName(item.log.actor_user_id)
              return (
                <div key={item.log.id} className="flex gap-3 group">
                  {/* Spine */}
                  <div className="flex flex-col items-center">
                    <Avatar className={cn("h-6 w-6 shrink-0", avatarColor(actorName))}>
                      <AvatarFallback className={cn("text-[10px] text-white", avatarColor(actorName))}>
                        {initials(actorName)}
                      </AvatarFallback>
                    </Avatar>
                    {!isLast && <div className="w-px flex-1 bg-border mt-1 mb-0.5 min-h-3" />}
                  </div>
                  {/* Content */}
                  <div className={cn("pb-3 flex-1 min-w-0 flex items-baseline gap-2 flex-wrap", isLast && "pb-0")}>
                    <span className="text-xs text-foreground">
                      <span className="font-semibold">{actorName}</span>
                      {" "}
                      <span className="text-muted-foreground">{activitySentence(item.log)}</span>
                    </span>
                    <span className="text-xs text-muted-foreground/60 shrink-0 whitespace-nowrap">
                      {relativeTime(item.log.created_at)}
                    </span>
                  </div>
                </div>
              )
            }

            // Comment item
            const authorName = resolveName(item.comment.author_user_id)
            return (
              <div key={item.comment.id} className="flex gap-3">
                {/* Spine */}
                <div className="flex flex-col items-center">
                  <Avatar className="h-6 w-6 shrink-0">
                    <AvatarFallback className={cn("text-[10px] text-white", avatarColor(authorName))}>
                      {initials(authorName)}
                    </AvatarFallback>
                  </Avatar>
                  {!isLast && <div className="w-px flex-1 bg-border mt-1 mb-0.5 min-h-3" />}
                </div>
                {/* Reuse CommentCard but pass the spine-aware class */}
                <div className="pb-3 flex-1 min-w-0">
                  <CommentCard
                    comment={item.comment}
                    orgId={orgId}
                    taskId={taskId}
                    authorName={authorName}
                  />
                </div>
              </div>
            )
          })}
          <div ref={bottomRef} />
        </div>
      )}

      <Separator />
      <CommentForm orgId={orgId} taskId={taskId} />
    </div>
  )
}

