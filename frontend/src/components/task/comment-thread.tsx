import { useEffect, useRef } from "react"
import { MessageSquare } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
import { CommentCard } from "./comment-card"
import { CommentForm } from "./comment-form"
import { useComments } from "@/hooks/use-comments"
import { useMembers } from "@/hooks/use-members"

interface CommentThreadProps {
  orgId: string
  taskId: string
}

export function CommentThread({ orgId, taskId }: CommentThreadProps) {
  const { data: comments = [], isLoading } = useComments(orgId, taskId)
  const { data: members = [] } = useMembers(orgId)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Scroll to bottom whenever new comments arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [comments.length])

  function resolveAuthorName(authorUserId: string | null): string {
    if (!authorUserId) return "Deleted user"
    const member = members.find((m) => m.user_id === authorUserId)
    return member?.full_name ?? member?.email ?? "Unknown"
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-2">
        <MessageSquare className="h-4 w-4 text-muted-foreground" />
        <p className="text-sm font-semibold">
          Comments
          {comments.length > 0 && (
            <span className="ml-1.5 text-xs font-normal text-muted-foreground">({comments.length})</span>
          )}
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[1, 2].map((i) => (
            <div key={i} className="flex gap-3">
              <Skeleton className="h-7 w-7 rounded-full shrink-0" />
              <div className="flex-1 space-y-1.5">
                <Skeleton className="h-3.5 w-24" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            </div>
          ))}
        </div>
      ) : comments.length === 0 ? (
        <p className="text-xs text-muted-foreground text-center py-4">
          No comments yet. Be the first to comment.
        </p>
      ) : (
        <ScrollArea className="max-h-80">
          <div className="space-y-4 pr-2">
            {comments.map((comment) => (
              <CommentCard
                key={comment.id}
                comment={comment}
                orgId={orgId}
                taskId={taskId}
                authorName={resolveAuthorName(comment.author_user_id)}
              />
            ))}
            <div ref={bottomRef} />
          </div>
        </ScrollArea>
      )}

      <Separator />
      <CommentForm orgId={orgId} taskId={taskId} />
    </div>
  )
}
