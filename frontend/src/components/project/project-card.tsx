import { useNavigate } from "react-router-dom"
import { ArrowRight, Calendar } from "lucide-react"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { ProjectStatusBadge } from "./project-status-badge"
import type { Project } from "@/types/project"
import { cn } from "@/lib/utils"

interface ProjectCardProps {
  project: Project
  orgId: string
  view?: "grid" | "list"
}

export function ProjectCard({ project, orgId, view = "grid" }: ProjectCardProps) {
  const navigate = useNavigate()

  if (view === "list") {
    return (
      <div
        className="flex items-center justify-between px-4 py-3 rounded-lg border bg-card transition-all duration-200 cursor-pointer group hover:bg-accent/50 dark:hover:border-primary/20 dark:hover:shadow-[0_0_10px_var(--neon-glow-spread)]"
        onClick={() => navigate(`/orgs/${orgId}/projects/${project.id}/board`)}
      >
        <div className="flex items-center gap-3 min-w-0">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 dark:bg-primary/15 text-primary font-bold text-sm">
            {project.name[0]?.toUpperCase()}
          </div>
          <div className="min-w-0">
            <p className="font-medium text-sm truncate">{project.name}</p>
            {project.description && (
              <p className="text-xs text-muted-foreground truncate">{project.description}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3 shrink-0 ml-4">
          <ProjectStatusBadge status={project.status} />
          <span className="text-xs text-muted-foreground">
            {new Date(project.created_at).toLocaleDateString()}
          </span>
          <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>
      </div>
    )
  }

  return (
    <Card
      className={cn("cursor-pointer group")}
      onClick={() => navigate(`/orgs/${orgId}/projects/${project.id}/board`)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 dark:bg-primary/15 text-primary font-bold text-base transition-all duration-200 dark:group-hover:shadow-[0_0_10px_var(--neon-glow-spread)]">
              {project.name[0]?.toUpperCase()}
            </div>
            <p className="font-semibold text-base leading-tight line-clamp-1">
              {project.name}
            </p>
          </div>
          <ProjectStatusBadge status={project.status} className="shrink-0 mt-0.5" />
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {project.description ? (
          <p className="text-sm text-muted-foreground line-clamp-2">{project.description}</p>
        ) : (
          <p className="text-sm text-muted-foreground/50 italic">No description</p>
        )}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Calendar className="h-3.5 w-3.5" />
            {new Date(project.created_at).toLocaleDateString()}
          </div>
          <ArrowRight className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>
      </CardContent>
    </Card>
  )
}
