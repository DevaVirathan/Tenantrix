import { useSortable } from "@dnd-kit/sortable"
import { CSS } from "@dnd-kit/utilities"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { PriorityIcon } from "./priority-icon"
import { IssueTypeIcon } from "./issue-type-icon"
import { LabelBadge } from "./label-badge"
import { useAppStore } from "@/store/app-store"
import { useMembers } from "@/hooks/use-members"
import type { Task } from "@/types/task"
import { cn } from "@/lib/utils"
import { CalendarDays, Hexagon } from "lucide-react"
import { format, isPast, isToday, addDays, isBefore } from "date-fns"

interface TaskCardProps {
  task: Task
  orgId: string
}

function initials(name: string) {
  return name.split(" ").map((w) => w[0]).join("").toUpperCase().slice(0, 2)
}

function dueDateColor(dueDateStr: string): string {
  const due = new Date(dueDateStr)
  if (isPast(due) && !isToday(due)) return "text-red-500"
  if (isToday(due) || isBefore(due, addDays(new Date(), 2))) return "text-yellow-500"
  return "text-muted-foreground"
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
      {/* Issue type + Title */}
      <div className="flex items-start gap-1.5 mb-2">
        <IssueTypeIcon type={task.issue_type} className="h-4 w-4 mt-0.5 shrink-0" />
        <p className="text-sm font-medium leading-snug line-clamp-2">{task.title}</p>
      </div>

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

      {/* Footer: priority + due date + story points + assignee */}
      <div className="flex items-center justify-between mt-1">
        <div className="flex items-center gap-2">
          <PriorityIcon priority={task.priority} showLabel />
          {task.due_date && (
            <span className={cn("flex items-center gap-0.5 text-[10px]", dueDateColor(task.due_date))}>
              <CalendarDays className="h-3 w-3" />
              {format(new Date(task.due_date), "MMM d")}
            </span>
          )}
          {task.story_points != null && (
            <span className="flex items-center gap-0.5 text-[10px] text-muted-foreground">
              <Hexagon className="h-3 w-3" />
              {task.story_points}
            </span>
          )}
        </div>
        {assigneeName && (
          <Avatar className="h-5 w-5">
            <AvatarFallback className="text-[10px]">{initials(assigneeName)}</AvatarFallback>
          </Avatar>
        )}
      </div>
    </div>
  )
}
