import { Badge } from "@/components/ui/badge"
import type { OrgRole } from "@/types/org"
import { cn } from "@/lib/utils"

const ROLE_STYLES: Record<OrgRole, string> = {
  owner:  "bg-purple-500/15 text-purple-400 border-purple-500/30",
  admin:  "bg-blue-500/15 text-blue-400 border-blue-500/30",
  member: "bg-green-500/15 text-green-400 border-green-500/30",
  viewer: "bg-gray-500/15 text-gray-400 border-gray-500/30",
}

interface RoleBadgeProps {
  role: OrgRole
  className?: string
}

export function RoleBadge({ role, className }: RoleBadgeProps) {
  return (
    <Badge
      variant="outline"
      className={cn("capitalize text-xs font-medium", ROLE_STYLES[role], className)}
    >
      {role}
    </Badge>
  )
}
