import { useParams } from "react-router-dom"
import { Plus, LayoutGrid, List, FolderOpen } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { ProjectCard } from "@/components/project/project-card"
import { CreateProjectDialog } from "@/components/project/create-project-dialog"
import { useProjects } from "@/hooks/use-projects"
import { useAppStore } from "@/store/app-store"
import { hasRole } from "@/lib/rbac"

export function ProjectsPage() {
  const { orgId = "" } = useParams<{ orgId: string }>()
  const { data: projects, isLoading } = useProjects(orgId)
  const projectView = useAppStore((s) => s.projectView)
  const setProjectView = useAppStore((s) => s.setProjectView)
  const membership = useAppStore((s) => s.activeMembership)

  const canCreate = hasRole(membership?.role, "member")

  return (
    <div className="max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold">Projects</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage your organization&apos;s projects.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setProjectView("grid")}
            className={projectView === "grid" ? "bg-accent" : ""}
            aria-label="Grid view"
          >
            <LayoutGrid className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setProjectView("list")}
            className={projectView === "list" ? "bg-accent" : ""}
            aria-label="List view"
          >
            <List className="h-4 w-4" />
          </Button>
          {canCreate && (
            <CreateProjectDialog orgId={orgId}>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                New project
              </Button>
            </CreateProjectDialog>
          )}
        </div>
      </div>

      {isLoading ? (
        <div className={projectView === "grid" ? "grid sm:grid-cols-2 lg:grid-cols-3 gap-4" : "grid gap-3"}>
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Skeleton key={i} className="h-36 w-full" />
          ))}
        </div>
      ) : projects && projects.length > 0 ? (
        <div className={projectView === "grid" ? "grid sm:grid-cols-2 lg:grid-cols-3 gap-4" : "grid gap-3"}>
          {projects.map((project) => (
            <ProjectCard key={project.id} project={project} orgId={orgId} view={projectView} />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed py-20 gap-4 text-center">
          <FolderOpen className="h-10 w-10 text-muted-foreground" />
          <div>
            <p className="font-medium">No projects yet</p>
            <p className="text-sm text-muted-foreground">Create a project to get started.</p>
          </div>
          {canCreate && (
            <CreateProjectDialog orgId={orgId}>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                New project
              </Button>
            </CreateProjectDialog>
          )}
        </div>
      )}
    </div>
  )
}
