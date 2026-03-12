export interface SavedView {
  id: string
  project_id: string
  org_id: string
  created_by_user_id: string
  name: string
  description: string | null
  filters: Record<string, unknown>
  view_type: "board" | "list" | "calendar" | "timeline"
  is_shared: boolean
  created_at: string
  updated_at: string
}

export interface SavedViewCreate {
  name: string
  description?: string
  filters: Record<string, unknown>
  view_type: string
  is_shared?: boolean
}
