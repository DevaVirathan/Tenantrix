import { z } from "zod"

const SPECIAL_RE = /[!@#$%^&*()\-_=+[\]{};:'",.<>/?\\|`~]/

export const loginSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(1, "Password is required"),
})

export const registerSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z
    .string()
    .min(8, "Minimum 8 characters")
    .max(128, "Maximum 128 characters")
    .refine((v) => /[a-z]/.test(v), { message: "Must contain a lowercase letter" })
    .refine((v) => /[A-Z]/.test(v), { message: "Must contain an uppercase letter" })
    .refine((v) => /\d/.test(v), { message: "Must contain a digit" })
    .refine((v) => SPECIAL_RE.test(v), { message: "Must contain a special character (!@#$%...)" }),
  full_name: z.string().max(255).optional(),
})

export type LoginFormValues = z.infer<typeof loginSchema>
export type RegisterFormValues = z.infer<typeof registerSchema>
