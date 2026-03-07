export type ProjectStatus = "active" | "archived"

export interface Project {
  id: string
  organization_id: string
  name: string
  description: string | null
  status: ProjectStatus
  created_at: string
  updated_at: string
}
