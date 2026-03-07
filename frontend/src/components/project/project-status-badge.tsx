import { Badge } from "@/components/ui/badge"
import type { ProjectStatus } from "@/types/project"
import { cn } from "@/lib/utils"

const STATUS_STYLES: Record<ProjectStatus, string> = {
  active:   "bg-green-500/15 text-green-400 border-green-500/30",
  archived: "bg-gray-500/15 text-gray-400 border-gray-500/30",
}

interface ProjectStatusBadgeProps {
  status: ProjectStatus
  className?: string
}

export function ProjectStatusBadge({ status, className }: ProjectStatusBadgeProps) {
  return (
    <Badge
      variant="outline"
      className={cn("capitalize text-xs font-medium", STATUS_STYLES[status], className)}
    >
      {status}
    </Badge>
  )
}
