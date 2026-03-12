export type StateGroup = "backlog" | "unstarted" | "started" | "completed" | "cancelled"

export interface ProjectState {
  id: string
  project_id: string
  name: string
  color: string
  group: StateGroup
  position: number
  is_default: boolean
  created_at: string
  updated_at: string
}

export const STATE_GROUP_LABELS: Record<StateGroup, string> = {
  backlog: "Backlog",
  unstarted: "Unstarted",
  started: "Started",
  completed: "Completed",
  cancelled: "Cancelled",
}
