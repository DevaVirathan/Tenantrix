import type { OrgRole } from "@/types/org"

const ROLE_RANK: Record<OrgRole, number> = {
  viewer: 0,
  member: 1,
  admin: 2,
  owner: 3,
}

/**
 * Returns true if `userRole` meets or exceeds the `required` role level.
 * Example: hasRole("admin", "member") === true
 */
export function hasRole(userRole: OrgRole | null | undefined, required: OrgRole): boolean {
  if (!userRole) return false
  return ROLE_RANK[userRole] >= ROLE_RANK[required]
}
