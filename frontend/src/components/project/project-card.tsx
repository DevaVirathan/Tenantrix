import { useNavigate } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ProjectStatusBadge } from "./project-status-badge"
import type { Project } from "@/types/project"

interface ProjectCardProps {
  project: Project
  orgId: string
}

export function ProjectCard({ project, orgId }: ProjectCardProps) {
  const navigate = useNavigate()

  return (
    <Card
      className="cursor-pointer hover:bg-accent/50 transition-colors"
      onClick={() => navigate(`/orgs/${orgId}/projects/${project.id}/board`)}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-base font-semibold leading-tight line-clamp-1">
            {project.name}
          </CardTitle>
          <ProjectStatusBadge status={project.status} className="shrink-0" />
        </div>
      </CardHeader>
      <CardContent>
        {project.description ? (
          <p className="text-sm text-muted-foreground line-clamp-2">{project.description}</p>
        ) : (
          <p className="text-sm text-muted-foreground italic">No description</p>
        )}
        <p className="text-xs text-muted-foreground mt-3">
          Created {new Date(project.created_at).toLocaleDateString()}
        </p>
      </CardContent>
    </Card>
  )
}
