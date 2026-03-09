import { useRef } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { SendHorizontal } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Form, FormControl, FormField, FormItem, FormMessage } from "@/components/ui/form"
import { useCreateComment } from "@/hooks/use-comments"
import { useAppStore } from "@/store/app-store"
import { hasRole } from "@/lib/rbac"
import { createCommentSchema, type CreateCommentValues } from "@/validations/comment.schema"
import { cn } from "@/lib/utils"

const AVATAR_COLORS = [
  "bg-blue-500", "bg-green-500", "bg-purple-500",
  "bg-orange-500", "bg-pink-500", "bg-teal-500",
]
function avatarColor(name: string) {
  let hash = 0
  for (const c of name) hash = (hash * 31 + c.charCodeAt(0)) % AVATAR_COLORS.length
  return AVATAR_COLORS[hash]
}
function initials(name: string) {
  return name.split(" ").map((w) => w[0]).join("").toUpperCase().slice(0, 2)
}

interface CommentFormProps {
  orgId: string
  taskId: string
}

export function CommentForm({ orgId, taskId }: CommentFormProps) {
  const user = useAppStore((s) => s.user)
  const membership = useAppStore((s) => s.activeMembership)
  const canComment = hasRole(membership?.role, "member")
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const { mutate: createComment, isPending } = useCreateComment(orgId, taskId)

  const form = useForm<CreateCommentValues>({
    resolver: zodResolver(createCommentSchema),
    defaultValues: { body: "" },
  })

  function onSubmit(values: CreateCommentValues) {
    createComment(values, {
      onSuccess: () => {
        form.reset()
        textareaRef.current?.focus()
      },
    })
  }

  const authorName = user?.full_name ?? user?.email ?? "You"

  if (!canComment) {
    return (
      <p className="text-xs text-muted-foreground text-center py-2">
        Viewers cannot post comments.
      </p>
    )
  }

  return (
    <div className="flex gap-3 pt-2">
      <Avatar className="h-7 w-7 shrink-0 mt-1">
        <AvatarFallback className={cn("text-[11px] text-white", avatarColor(authorName))}>
          {initials(authorName)}
        </AvatarFallback>
      </Avatar>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="flex-1 space-y-2">
          <FormField
            control={form.control}
            name="body"
            render={({ field }) => (
              <FormItem>
                <FormControl>
                  <Textarea
                    placeholder="Write a comment… (Ctrl+Enter to send)"
                    className="min-h-16 text-sm resize-none"
                    disabled={isPending}
                    {...field}
                    ref={(el) => {
                      field.ref(el)
                      textareaRef.current = el
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                        form.handleSubmit(onSubmit)()
                      }
                    }}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <div className="flex justify-end">
            <Button
              type="submit"
              size="sm"
              className="gap-1.5"
              disabled={isPending || !form.watch("body").trim()}
            >
              <SendHorizontal className="h-3.5 w-3.5" />
              {isPending ? "Posting…" : "Comment"}
            </Button>
          </div>
        </form>
      </Form>
    </div>
  )
}
