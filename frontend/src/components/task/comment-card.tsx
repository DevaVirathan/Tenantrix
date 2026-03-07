import { useState } from "react"
import { Pencil, Trash2, Check, X } from "lucide-react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { useUpdateComment, useDeleteComment } from "@/hooks/use-comments"
import { useAppStore } from "@/store/app-store"
import { hasRole } from "@/lib/rbac"
import type { Comment } from "@/types/comment"
import { cn } from "@/lib/utils"

interface CommentCardProps {
  comment: Comment
  orgId: string
  taskId: string
  authorName: string
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
  return new Date(iso).toLocaleDateString()
}

function initials(name: string) {
  return name.split(" ").map((w) => w[0]).join("").toUpperCase().slice(0, 2)
}

// Consistent colour from name
const AVATAR_COLORS = [
  "bg-blue-500", "bg-green-500", "bg-purple-500",
  "bg-orange-500", "bg-pink-500", "bg-teal-500",
]
function avatarColor(name: string) {
  let hash = 0
  for (const c of name) hash = (hash * 31 + c.charCodeAt(0)) % AVATAR_COLORS.length
  return AVATAR_COLORS[hash]
}

export function CommentCard({ comment, orgId, taskId, authorName }: CommentCardProps) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(comment.body)

  const user = useAppStore((s) => s.user)
  const membership = useAppStore((s) => s.activeMembership)

  const isAuthor = user?.id === comment.author_user_id
  const isAdminPlus = hasRole(membership?.role, "admin")
  const canEdit = isAuthor && hasRole(membership?.role, "member")
  const canDelete = isAuthor || isAdminPlus

  const { mutate: updateComment, isPending: isUpdating } = useUpdateComment(orgId, taskId)
  const { mutate: deleteComment, isPending: isDeleting } = useDeleteComment(orgId, taskId)

  function handleSave() {
    const trimmed = draft.trim()
    if (!trimmed || trimmed === comment.body) { setEditing(false); return }
    updateComment(
      { commentId: comment.id, data: { body: trimmed } },
      { onSuccess: () => setEditing(false) }
    )
  }

  function handleDiscard() {
    setDraft(comment.body)
    setEditing(false)
  }

  function handleDelete() {
    if (!confirm("Delete this comment?")) return
    deleteComment(comment.id)
  }

  return (
    <div className="flex gap-3 group">
      {/* Avatar */}
      <Avatar className="h-7 w-7 shrink-0 mt-0.5">
        <AvatarFallback className={cn("text-[11px] text-white", avatarColor(authorName))}>
          {initials(authorName)}
        </AvatarFallback>
      </Avatar>

      <div className="flex-1 min-w-0">
        {/* Header */}
        <div className="flex items-baseline gap-2 mb-1">
          <span className="text-sm font-semibold truncate">{authorName}</span>
          <span className="text-xs text-muted-foreground shrink-0">{relativeTime(comment.created_at)}</span>
          {comment.updated_at !== comment.created_at && (
            <span className="text-xs text-muted-foreground shrink-0">(edited)</span>
          )}
        </div>

        {/* Body — view or inline edit */}
        {editing ? (
          <div className="space-y-2">
            <Textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              className="min-h-20 text-sm resize-none"
              autoFocus
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleSave()
                if (e.key === "Escape") handleDiscard()
              }}
            />
            <div className="flex gap-1.5">
              <Button size="sm" className="h-7 gap-1 text-xs" onClick={handleSave} disabled={isUpdating}>
                <Check className="h-3 w-3" />
                {isUpdating ? "Saving…" : "Save"}
              </Button>
              <Button size="sm" variant="ghost" className="h-7 gap-1 text-xs" onClick={handleDiscard}>
                <X className="h-3 w-3" />
                Discard
              </Button>
            </div>
          </div>
        ) : (
          <p className="text-sm whitespace-pre-wrap break-words text-foreground/90">{comment.body}</p>
        )}
      </div>

      {/* Action buttons — shown on hover */}
      {!editing && (
        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0 pt-0.5">
          {canEdit && (
            <Button
              variant="ghost" size="icon"
              className="h-6 w-6 text-muted-foreground hover:text-foreground"
              onClick={() => setEditing(true)}
              aria-label="Edit comment"
            >
              <Pencil className="h-3 w-3" />
            </Button>
          )}
          {canDelete && (
            <Button
              variant="ghost" size="icon"
              className="h-6 w-6 text-muted-foreground hover:text-destructive"
              onClick={handleDelete}
              disabled={isDeleting}
              aria-label="Delete comment"
            >
              <Trash2 className="h-3 w-3" />
            </Button>
          )}
        </div>
      )}
    </div>
  )
}
