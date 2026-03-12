import { z } from "zod"

export const createTaskSchema = z.object({
  title: z.string().min(1, "Title is required").max(500),
  description: z.string().max(5000).optional(),
  status: z.enum(["todo", "in_progress", "done", "blocked"]),
  priority: z.enum(["low", "medium", "high", "urgent"]),
  issue_type: z.enum(["bug", "story", "epic", "task", "subtask"]).optional(),
  assignee_user_id: z.string().uuid().nullable().optional(),
  parent_task_id: z.string().uuid().nullable().optional(),
  sprint_id: z.string().uuid().nullable().optional(),
  module_id: z.string().uuid().nullable().optional(),
  state_id: z.string().uuid().nullable().optional(),
  position: z.number().int().min(0).optional(),
  story_points: z.number().int().min(0).max(100).nullable().optional(),
  start_date: z.string().nullable().optional(),
  due_date: z.string().nullable().optional(),
})

export const updateTaskSchema = z.object({
  title: z.string().min(1).max(500).optional(),
  description: z.string().max(5000).nullable().optional(),
  status: z.enum(["todo", "in_progress", "done", "blocked"]).optional(),
  state_id: z.string().uuid().nullable().optional(),
  priority: z.enum(["low", "medium", "high", "urgent"]).optional(),
  issue_type: z.enum(["bug", "story", "epic", "task", "subtask"]).optional(),
  assignee_user_id: z.string().uuid().nullable().optional(),
  parent_task_id: z.string().uuid().nullable().optional(),
  sprint_id: z.string().uuid().nullable().optional(),
  module_id: z.string().uuid().nullable().optional(),
  position: z.number().int().min(0).optional(),
  story_points: z.number().int().min(0).max(100).nullable().optional(),
  start_date: z.string().nullable().optional(),
  due_date: z.string().nullable().optional(),
})

export const createLabelSchema = z.object({
  name: z.string().min(1).max(100),
  color: z
    .string()
    .regex(/^#[0-9A-Fa-f]{6}$/, "Must be a valid hex color")
    .optional(),
})

export type CreateTaskValues = z.infer<typeof createTaskSchema>
export type UpdateTaskValues = z.infer<typeof updateTaskSchema>
export type CreateLabelValues = z.infer<typeof createLabelSchema>
