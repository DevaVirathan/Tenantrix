export type TaskStatus = "todo" | "in_progress" | "done" | "blocked"
export type TaskPriority = "low" | "medium" | "high" | "urgent"

export interface Label {
  id: string
  organization_id: string
  name: string
  color: string | null
}

export interface Task {
  id: string
  organization_id: string
  project_id: string
  assignee_user_id: string | null
  title: string
  description: string | null
  status: TaskStatus
  priority: TaskPriority
  position: number
  labels: Label[]
  deleted_at: string | null
  created_at: string
  updated_at: string
}

export interface TaskFilters {
  status?: TaskStatus
  priority?: TaskPriority
  assignee_user_id?: string
}

export const TASK_STATUS_LABELS: Record<TaskStatus, string> = {
  todo: "Todo",
  in_progress: "In Progress",
  done: "Done",
  blocked: "Blocked",
}

export const TASK_PRIORITY_LABELS: Record<TaskPriority, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
  urgent: "Urgent",
}

export const KANBAN_COLUMNS: TaskStatus[] = ["todo", "in_progress", "done", "blocked"]
