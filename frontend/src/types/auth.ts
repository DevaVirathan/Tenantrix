export interface User {
  id: string
  email: string
  full_name: string | null
  is_active: boolean
  created_at: string
}

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: "bearer"
  expires_in: number
}

export interface MessageOut {
  message: string
}
