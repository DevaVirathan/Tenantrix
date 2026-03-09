import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
import { formatDistanceToNow, format, parseISO } from "date-fns"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatRelative(isoString: string): string {
  return formatDistanceToNow(parseISO(isoString), { addSuffix: true })
}

export function formatDate(isoString: string, fmt = "MMM d, yyyy"): string {
  return format(parseISO(isoString), fmt)
}

export function getInitials(name: string | null | undefined, email: string): string {
  if (name) {
    const parts = name.trim().split(/\s+/).filter(Boolean)
    if (parts.length > 0) {
      return parts.map((n) => n[0]).join("").toUpperCase().slice(0, 2)
    }
  }
  if (email && email.length > 0) {
    return email[0].toUpperCase()
  }
  return "?"
}
