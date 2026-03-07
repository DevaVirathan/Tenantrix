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
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2)
  }
  return email[0].toUpperCase()
}
