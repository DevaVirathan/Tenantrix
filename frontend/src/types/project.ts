export type ProjectStatus = "active" | "archived"

export interface Project {
  id: string
  organization_id: string
  name: string
  description: string | null
  identifier: string | null
  issue_sequence: number
  status: ProjectStatus
  created_at: string
  updated_at: string
}
