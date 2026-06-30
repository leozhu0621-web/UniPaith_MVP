// AUTO-SPLIT from the former monolithic types/index.ts.
// Domain module — see CONTRIBUTING.md. Edit types here, not in a barrel.
// === AUTH ===
export interface User {
  id: string
  email: string
  role: 'student' | 'institution_admin'
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string | null
  expires_in: number
  token_type: string
}
