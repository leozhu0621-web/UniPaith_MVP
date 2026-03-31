import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

let isRefreshing = false
let refreshSubscribers: ((token: string) => void)[] = []

function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb)
}

function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach(cb => cb(token))
  refreshSubscribers = []
}

// Lazy-loaded to break circular dep (auth-store imports client, client needs auth-store)
let _useAuthStore: any = null
async function loadAuthStore() {
  if (!_useAuthStore) {
    const mod = await import('../stores/auth-store')
    _useAuthStore = mod.useAuthStore
  }
  return _useAuthStore
}

apiClient.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
  const store = await loadAuthStore()
  const token = store.getState().accessToken
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  response => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      const store = await loadAuthStore()

      if (isRefreshing) {
        return new Promise(resolve => {
          subscribeTokenRefresh((token: string) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`
            }
            resolve(apiClient(originalRequest))
          })
        })
      }

      isRefreshing = true

      try {
        const newToken = await store.getState().refreshAccessToken()
        isRefreshing = false
        onTokenRefreshed(newToken)
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`
        }
        return apiClient(originalRequest)
      } catch {
        isRefreshing = false
        store.getState().logout()
        window.location.href = '/login'
        return Promise.reject(error)
      }
    }

    const message = (error.response?.data as any)?.detail || error.message
    return Promise.reject(new Error(message))
  }
)

export default apiClient
