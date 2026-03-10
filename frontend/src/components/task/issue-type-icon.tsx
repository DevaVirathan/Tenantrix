import { Bug, BookOpen, Layers, CheckSquare, ListTree } from "lucide-react"
import type { IssueType } from "@/types/task"
import { cn } from "@/lib/utils"

const CONFIG: Record<IssueType, { icon: React.ElementType; className: string }> = {
  bug:     { icon: Bug,         className: "text-red-500" },
  story:   { icon: BookOpen,    className: "text-green-500" },
  epic:    { icon: Layers,      className: "text-purple-500" },
  task:    { icon: CheckSquare, className: "text-blue-500" },
  subtask: { icon: ListTree,    className: "text-gray-400" },
}

interface IssueTypeIconProps {
  type: IssueType
  className?: string
  showLabel?: boolean
}

export function IssueTypeIcon({ type, className, showLabel }: IssueTypeIconProps) {
  const { icon: Icon, className: color } = CONFIG[type]
  return (
    <span className={cn("inline-flex items-center gap-1", color)}>
      <Icon className={cn("h-3.5 w-3.5", className)} />
      {showLabel && <span className="text-xs capitalize">{type.replace("_", "-")}</span>}
    </span>
  )
}
