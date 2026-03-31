import { create } from 'zustand'
import apiClient from '../api/client'

interface User {
  id: string
  email: string
  role: 'student' | 'institution_admin' | 'admin'
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
  logout: () => void
  refreshAccessToken: () => Promise<string>
  loadSession: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  refreshToken: localStorage.getItem('unipaith_refresh_token'),
  isAuthenticated: false,
  isLoading: true,

  login: async (email, password) => {
    const { data } = await apiClient.post('/auth/login', { email, password })
    set({ accessToken: data.access_token, refreshToken: data.refresh_token })
    localStorage.setItem('unipaith_refresh_token', data.refresh_token)

    const { data: user } = await apiClient.get('/auth/me', {
      headers: { Authorization: `Bearer ${data.access_token}` },
    })
    set({
      user: { id: user.user_id, email: user.email, role: user.role, created_at: user.created_at },
      isAuthenticated: true,
    })
  },

  signup: async (email, password, role) => {
    await apiClient.post('/auth/signup', { email, password, role })
    await get().login(email, password)
  },

  logout: () => {
    localStorage.removeItem('unipaith_refresh_token')
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
        user: { id: user.user_id, email: user.email, role: user.role, created_at: user.created_at },
        isAuthenticated: true,
        isLoading: false,
      })
    } catch {
      get().logout()
      set({ isLoading: false })
    }
  },
}))
