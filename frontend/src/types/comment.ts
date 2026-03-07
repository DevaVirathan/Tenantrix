export interface Comment {
  id: string
  organization_id: string
  task_id: string
  author_user_id: string | null
  body: string
  deleted_at: string | null
  created_at: string
  updated_at: string
}
