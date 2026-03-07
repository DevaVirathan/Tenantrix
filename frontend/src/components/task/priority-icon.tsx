import { cn } from "@/lib/utils"
import type { TaskPriority } from "@/types/task"
import { ArrowDown, ArrowRight, ArrowUp, AlertCircle } from "lucide-react"

const PRIORITY_CONFIG: Record<
  TaskPriority,
  { icon: React.ElementType; className: string; label: string }
> = {
  low:    { icon: ArrowDown,    className: "text-gray-400",   label: "Low" },
  medium: { icon: ArrowRight,   className: "text-yellow-400", label: "Medium" },
  high:   { icon: ArrowUp,      className: "text-orange-400", label: "High" },
  urgent: { icon: AlertCircle,  className: "text-red-400",    label: "Urgent" },
}

interface PriorityIconProps {
  priority: TaskPriority
  className?: string
  showLabel?: boolean
}

export function PriorityIcon({ priority, className, showLabel }: PriorityIconProps) {
  const { icon: Icon, className: colorClass, label } = PRIORITY_CONFIG[priority]
  return (
    <span className={cn("inline-flex items-center gap-1", className)}>
      <Icon className={cn("h-3.5 w-3.5", colorClass)} />
      {showLabel && <span className={cn("text-xs", colorClass)}>{label}</span>}
    </span>
  )
}
