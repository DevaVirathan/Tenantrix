import { useSortable } from "@dnd-kit/sortable"
import { CSS } from "@dnd-kit/utilities"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { PriorityIcon } from "./priority-icon"
import { LabelBadge } from "./label-badge"
import { useAppStore } from "@/store/app-store"
import { useMembers } from "@/hooks/use-members"
import type { Task } from "@/types/task"
import { cn } from "@/lib/utils"

interface TaskCardProps {
  task: Task
  orgId: string
}

function initials(name: string) {
  return name.split(" ").map((w) => w[0]).join("").toUpperCase().slice(0, 2)
}

export function TaskCard({ task, orgId }: TaskCardProps) {
  const openTaskPanel = useAppStore((s) => s.openTaskPanel)
  const { data: members = [] } = useMembers(orgId)

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: task.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  const assignee = task.assignee_user_id
    ? members.find((m) => m.user_id === task.assignee_user_id)
    : null

  const assigneeName = assignee
    ? (assignee.full_name ?? assignee.email ?? assignee.user_id)
    : null

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={cn(
        "group rounded-md border bg-card p-3 shadow-sm cursor-grab active:cursor-grabbing",
        "hover:border-primary/50 transition-colors select-none",
        isDragging && "opacity-50 ring-2 ring-primary/30"
      )}
      onClick={() => openTaskPanel(task.id)}
    >
      {/* Title */}
      <p className="text-sm font-medium leading-snug line-clamp-2 mb-2">{task.title}</p>

      {/* Labels */}
      {task.labels.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {task.labels.slice(0, 3).map((label) => (
            <LabelBadge key={label.id} label={label} />
          ))}
          {task.labels.length > 3 && (
            <span className="text-xs text-muted-foreground">+{task.labels.length - 3}</span>
          )}
        </div>
      )}

      {/* Footer: priority + assignee */}
      <div className="flex items-center justify-between mt-1">
        <PriorityIcon priority={task.priority} showLabel />
        {assigneeName && (
          <Avatar className="h-5 w-5">
            <AvatarFallback className="text-[10px]">{initials(assigneeName)}</AvatarFallback>
          </Avatar>
        )}
      </div>
    </div>
  )
}
