import { z } from "zod"

export const createOrgSchema = z.object({
  name: z.string().min(1, "Name is required").max(255),
  slug: z
    .string()
    .min(2, "Slug must be at least 2 characters")
    .max(100)
    .regex(/^[a-z0-9-]+$/, "Slug can only contain lowercase letters, numbers and hyphens"),
  description: z.string().max(1000).optional(),
})

export const updateOrgSchema = z.object({
  name: z.string().min(1).max(255).optional(),
  description: z.string().max(1000).nullable().optional(),
})

export const createInviteSchema = z.object({
  email: z.string().email("Invalid email address"),
  role: z.enum(["owner", "admin", "member", "viewer"]),
})

export type CreateOrgValues = z.infer<typeof createOrgSchema>
export type UpdateOrgValues = z.infer<typeof updateOrgSchema>
export type CreateInviteValues = z.infer<typeof createInviteSchema>
