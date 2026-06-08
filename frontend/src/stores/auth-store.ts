import { create } from 'zustand'
import apiClient from '../api/client'
import { clearSignalEdits } from '../pages/student/discover/noticed'

const REFRESH_TOKEN_KEY = 'unipaith_refresh_token'

function readRefreshToken(): string | null {
  const tabToken = sessionStorage.getItem(REFRESH_TOKEN_KEY)
  if (tabToken) return tabToken

  // One-time migration path from legacy localStorage token.
  const legacyToken = localStorage.getItem(REFRESH_TOKEN_KEY)
  if (legacyToken) {
    sessionStorage.setItem(REFRESH_TOKEN_KEY, legacyToken)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    return legacyToken
  }
  return null
}

function persistRefreshToken(token: string | null) {
  if (token) {
    sessionStorage.setItem(REFRESH_TOKEN_KEY, token)
  } else {
    sessionStorage.removeItem(REFRESH_TOKEN_KEY)
  }
  // Keep legacy key cleared to avoid cross-tab role/session bleed.
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

interface User {
  id: string
  email: string
  role: 'student' | 'institution_admin'
  // True when this account is on the server-side owner allowlist; unlocks the
  // in-app feedback inbox (/s/feedback) and its nav link. Computed by /auth/me.
  is_owner?: boolean
  // Mirrors the backend ai_uni_guided_v1 flag; gates the guided Uni workspace
  // shell so flag-off keeps the single-column open Uni experience. From /auth/me.
  uni_guided?: boolean
  created_at: string
}

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean

  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string, role: string) => Promise<void>
  googleCallback: (code: string, redirectUri: string, role: string) => Promise<void>
  googleLogin: (idToken: string) => Promise<void>
  logout: () => void
  refreshAccessToken: () => Promise<string>
  loadSession: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  refreshToken: readRefreshToken(),
  isAuthenticated: false,
  isLoading: true,

  login: async (email, password) => {
    const { data } = await apiClient.post('/auth/login', { email, password })
    const loginUser = data?.user
    const normalizedUser = loginUser
      ? {
          id: String(loginUser.user_id ?? loginUser.id ?? ''),
          email: String(loginUser.email ?? email),
          role: loginUser.role as User['role'],
          created_at: String(loginUser.created_at ?? new Date().toISOString()),
          is_owner: Boolean(loginUser.is_owner),
          uni_guided: Boolean(loginUser.uni_guided),
        }
      : null

    // Backward-compatible path: some environments may return tokens without user payload.
    // In that case, fetch /auth/me immediately to populate session identity.
    const resolvedUser = normalizedUser?.id
      ? normalizedUser
      : await (async () => {
          const meToken = data?.access_token
          if (!meToken) {
            throw new Error('Login succeeded but access token is missing')
          }
          const { data: me } = await apiClient.get('/auth/me', {
            headers: { Authorization: `Bearer ${meToken}` },
          })
          return {
            id: String(me.user_id ?? me.id),
            email: String(me.email ?? email),
            role: me.role as User['role'],
            created_at: String(me.created_at ?? new Date().toISOString()),
            is_owner: Boolean(me.is_owner),
            uni_guided: Boolean(me.uni_guided),
          }
        })()

    // Drop any cached inline "Noticed" edits from a prior account on this SPA
    // session so the new user can't inherit stale signal→row links.
    clearSignalEdits()
    set({
      accessToken: data.access_token,
      refreshToken: data.refresh_token ?? null,
      user: resolvedUser,
      isAuthenticated: true,
    })
    persistRefreshToken(data.refresh_token ?? null)
  },

  signup: async (email, password, role) => {
    await apiClient.post('/auth/signup', { email, password, role })
    await get().login(email, password)
  },

  googleCallback: async (code, redirectUri, role) => {
    const { data } = await apiClient.post('/auth/google-callback', {
      code,
      redirect_uri: redirectUri,
      role,
    })
    const loginUser = data?.user
    const normalizedUser = loginUser
      ? {
          id: String(loginUser.user_id ?? loginUser.id ?? ''),
          email: String(loginUser.email ?? ''),
          role: loginUser.role as User['role'],
          created_at: String(loginUser.created_at ?? new Date().toISOString()),
          is_owner: Boolean(loginUser.is_owner),
          uni_guided: Boolean(loginUser.uni_guided),
        }
      : null

    clearSignalEdits()
    set({
      accessToken: data.access_token,
      refreshToken: data.refresh_token ?? null,
      user: normalizedUser,
      isAuthenticated: true,
    })
    persistRefreshToken(data.refresh_token ?? null)
  },

  googleLogin: async (idToken) => {
    const { data } = await apiClient.post('/auth/google', { id_token: idToken, role: 'student' })
    const loginUser = data?.user
    const normalizedUser = loginUser
      ? {
          id: String(loginUser.user_id ?? loginUser.id ?? ''),
          email: String(loginUser.email ?? ''),
          role: loginUser.role as User['role'],
          created_at: String(loginUser.created_at ?? new Date().toISOString()),
          is_owner: Boolean(loginUser.is_owner),
          uni_guided: Boolean(loginUser.uni_guided),
        }
      : null

    clearSignalEdits()
    set({
      accessToken: data.access_token,
      refreshToken: data.refresh_token ?? null,
      user: normalizedUser,
      isAuthenticated: true,
    })
    persistRefreshToken(data.refresh_token ?? null)
  },

  logout: () => {
    persistRefreshToken(null)
    // Drop any cached inline "Noticed" edits so the next user on this SPA session
    // can't inherit stale signal→row links.
    clearSignalEdits()
    set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false, isLoading: false })
  },

  refreshAccessToken: async () => {
    const rt = get().refreshToken
    if (!rt) throw new Error('No refresh token')
    const { data } = await apiClient.post('/auth/refresh', { refresh_token: rt })
    set({ accessToken: data.access_token })
    return data.access_token
  },

  loadSession: async () => {
    const rt = get().refreshToken
    if (!rt) {
      set({ isLoading: false })
      return
    }
    try {
      const token = await get().refreshAccessToken()
      const { data: user } = await apiClient.get('/auth/me', {
        headers: { Authorization: `Bearer ${token}` },
      })
      set({
        user: {
          id: user.user_id,
          email: user.email,
          role: user.role,
          created_at: user.created_at,
          is_owner: Boolean(user.is_owner),
          uni_guided: Boolean(user.uni_guided),
        },
        isAuthenticated: true,
        isLoading: false,
      })
    } catch {
      get().logout()
      set({ isLoading: false })
    }
  },
}))
