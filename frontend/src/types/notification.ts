export interface Notification {
  id: string
  recipient_user_id: string
  actor_user_id: string | null
  organization_id: string
  action_type: string
  resource_type: string
  resource_id: string
  message: string
  read_at: string | null
  created_at: string
}
