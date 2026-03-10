export type TaskStatus = "todo" | "in_progress" | "done" | "blocked"
export type TaskPriority = "low" | "medium" | "high" | "urgent"
export type IssueType = "bug" | "story" | "epic" | "task" | "subtask"

export interface Label {
  id: string
  organization_id: string
  name: string
  color: string | null
}

export type LinkType = "blocks" | "is_blocked_by" | "relates_to" | "duplicate_of"

export interface TaskSummary {
  id: string
  title: string
  status: TaskStatus
  issue_type: IssueType
}

export interface TaskLinkOut {
  id: string
  link_type: LinkType
  source_task: TaskSummary
  target_task: TaskSummary
  created_at: string
}

export interface Task {
  id: string
  organization_id: string
  project_id: string
  assignee_user_id: string | null
  created_by_user_id: string | null
  parent_task_id: string | null
  sprint_id: string | null
  module_id: string | null
  title: string
  description: string | null
  status: TaskStatus
  priority: TaskPriority
  issue_type: IssueType
  position: number
  story_points: number | null
  start_date: string | null
  due_date: string | null
  labels: Label[]
  parent: TaskSummary | null
  subtasks: TaskSummary[]
  links: TaskLinkOut[]
  deleted_at: string | null
  created_at: string
  updated_at: string
}

export interface TaskFilters {
  status?: TaskStatus
  priority?: TaskPriority
  assignee_user_id?: string
  issue_type?: IssueType
  sprint_id?: string
  no_sprint?: boolean
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

export const ISSUE_TYPE_LABELS: Record<IssueType, string> = {
  bug: "Bug",
  story: "Story",
  epic: "Epic",
  task: "Task",
  subtask: "Sub-task",
}

export const LINK_TYPE_LABELS: Record<LinkType, string> = {
  blocks: "Blocks",
  is_blocked_by: "Is blocked by",
  relates_to: "Relates to",
  duplicate_of: "Duplicate of",
}

export const KANBAN_COLUMNS: TaskStatus[] = ["todo", "in_progress", "done", "blocked"]
