import { z } from "zod"

export const createCommentSchema = z.object({
  body: z.string().min(1, "Comment cannot be empty").max(10000),
})

export const updateCommentSchema = z.object({
  body: z.string().min(1, "Comment cannot be empty").max(10000),
})

export type CreateCommentValues = z.infer<typeof createCommentSchema>
export type UpdateCommentValues = z.infer<typeof updateCommentSchema>
