export type ModuleStatus = "active" | "closed"

export interface Module {
  id: string
  organization_id: string
  project_id: string
  name: string
  description: string | null
  status: ModuleStatus
  start_date: string | null
  end_date: string | null
  task_count: number
  done_count: number
  total_points: number
  created_at: string
  updated_at: string
}
