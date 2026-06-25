import { create } from 'zustand'
import apiClient from '../api/client'
import { clearSignalEdits } from '../pages/student/discover/noticed'

const REFRESH_TOKEN_KEY = 'unipaith_refresh_token'

function readRefreshToken(): string | null {
  // Persist the refresh token in localStorage so a returning student stays signed
  // in across browser restarts (todo 1.3 — "make people stay signed in"). The
  // refresh token alone can't bleed identity: every session rehydrates the user
  // from /auth/me, and login/logout call clearSignalEdits() to drop per-account
  // cached edits. Migrate any legacy per-tab sessionStorage token forward.
  const stored = localStorage.getItem(REFRESH_TOKEN_KEY)
  if (stored) return stored
  const legacyTab = sessionStorage.getItem(REFRESH_TOKEN_KEY)
  if (legacyTab) {
    localStorage.setItem(REFRESH_TOKEN_KEY, legacyTab)
    sessionStorage.removeItem(REFRESH_TOKEN_KEY)
    return legacyTab
  }
  return null
}

function persistRefreshToken(token: string | null) {
  if (token) {
    localStorage.setItem(REFRESH_TOKEN_KEY, token)
  } else {
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  }
  // Drop any legacy per-tab copy so the two stores can't diverge.
  sessionStorage.removeItem(REFRESH_TOKEN_KEY)
}

// ── Proactive token renewal ───────────────────────────────────────────────
// Cognito access tokens live ~1h; without a proactive renew the student would be
// silently logged out after idle (the reactive 401 path only fires on the next
// request, and the SSE chat path can miss it). Renew a couple of minutes before
// expiry so the 1h TTL is invisible. The timer is cleared on logout.
let refreshTimer: ReturnType<typeof setTimeout> | null = null
const RENEW_LEAD_SEC = 120

function clearRefreshTimer() {
  if (refreshTimer) {
    clearTimeout(refreshTimer)
    refreshTimer = null
  }
}

function scheduleProactiveRefresh(expiresInSec: number | undefined, refresh: () => Promise<unknown>) {
  clearRefreshTimer()
  const ttl =
    typeof expiresInSec === 'number' && expiresInSec > RENEW_LEAD_SEC ? expiresInSec : 600
  refreshTimer = setTimeout(
    () => {
      // On failure the reactive 401 interceptor is still the safety net.
      void refresh().catch(() => {})
    },
    (ttl - RENEW_LEAD_SEC) * 1000,
  )
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
  signup: (email: string, password: string, role: string, firstName?: string) => Promise<void>
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
    scheduleProactiveRefresh(data.expires_in, () => get().refreshAccessToken())
  },

  signup: async (email, password, role, firstName) => {
    await apiClient.post('/auth/signup', { email, password, role, first_name: firstName })
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
    scheduleProactiveRefresh(data.expires_in, () => get().refreshAccessToken())
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
    scheduleProactiveRefresh(data.expires_in, () => get().refreshAccessToken())
  },

  logout: () => {
    clearRefreshTimer()
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
    // Re-arm the proactive timer off the fresh token's lifetime.
    scheduleProactiveRefresh(data.expires_in, () => get().refreshAccessToken())
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
    } catch (err) {
      // Only end the session on a real auth failure (invalid/expired refresh
      // token → 400/401). A transient network/5xx blip on boot must NOT log the
      // student out and dump them at /login — keep the refresh token so the next
      // request's interceptor can retry once the network recovers.
      const status = (err as { response?: { status?: number } })?.response?.status
      if (status === 400 || status === 401) {
        get().logout()
      }
      set({ isLoading: false })
    }
  },
}))
