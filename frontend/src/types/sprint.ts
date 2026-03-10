export type SprintStatus = "backlog" | "active" | "closed"

export interface Sprint {
  id: string
  organization_id: string
  project_id: string
  name: string
  description: string | null
  status: SprintStatus
  start_date: string | null
  end_date: string | null
  goals: string | null
  task_count: number
  done_count: number
  total_points: number
  created_at: string
  updated_at: string
}

export const SPRINT_STATUS_LABELS: Record<SprintStatus, string> = {
  backlog: "Backlog",
  active: "Active",
  closed: "Closed",
}
