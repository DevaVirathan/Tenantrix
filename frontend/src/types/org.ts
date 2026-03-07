export type OrgRole = "owner" | "admin" | "member" | "viewer"

export interface Organization {
  id: string
  name: string
  slug: string
  description: string | null
  created_by_user_id: string | null
  created_at: string
  updated_at: string
}

export interface Member {
  user_id: string
  role: OrgRole
  status: string
  joined_at: string
  // Joined from user table via backend (full_name/email not in MemberOut — enriched client-side)
  full_name?: string | null
  email?: string
}

export interface Invite {
  id: string
  organization_id: string
  email: string
  role: OrgRole
  token: string
  expires_at: string
}
