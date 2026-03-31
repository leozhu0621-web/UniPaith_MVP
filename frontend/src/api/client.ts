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

// Lazy import to break circular dep with auth-store
let _getAuthStore: (() => any) | null = null
function getAuthStore() {
  if (!_getAuthStore) {
    _getAuthStore = () => require('../stores/auth-store').useAuthStore.getState()
  }
  return _getAuthStore()
}

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAuthStore().accessToken
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
        const newToken = await getAuthStore().refreshAccessToken()
        isRefreshing = false
        onTokenRefreshed(newToken)
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`
        }
        return apiClient(originalRequest)
      } catch {
        isRefreshing = false
        getAuthStore().logout()
        window.location.href = '/login'
        return Promise.reject(error)
      }
    }

    const message = (error.response?.data as any)?.detail || error.message
    return Promise.reject(new Error(message))
  }
)

export default apiClient
