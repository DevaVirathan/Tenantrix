export interface AuditLog {
  id: string
  organization_id: string
  actor_user_id: string | null
  action: string
  resource_type: string | null
  resource_id: string | null
  metadata: Record<string, unknown> | null
  created_at: string
}

export interface AuditFilters {
  action?: string
  resource_type?: string
  actor_user_id?: string
  since?: string
  until?: string
  limit?: number
  offset?: number
}
