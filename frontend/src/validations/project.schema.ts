import { z } from "zod"

export const createProjectSchema = z.object({
  name: z.string().min(1, "Name is required").max(255),
  description: z.string().max(2000).optional(),
  status: z.enum(["active", "archived"]),
})

export const updateProjectSchema = z.object({
  name: z.string().min(1).max(255).optional(),
  description: z.string().max(2000).nullable().optional(),
  status: z.enum(["active", "archived"]).optional(),
})

export type CreateProjectValues = z.infer<typeof createProjectSchema>
export type UpdateProjectValues = z.infer<typeof updateProjectSchema>
