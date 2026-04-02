import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
  timeout: 30_000,
})

let isRefreshing = false

type RefreshWaiter = { resolve: (token: string) => void; reject: (err: unknown) => void }

const refreshWaiters: RefreshWaiter[] = []

function subscribeTokenRefresh(waiter: RefreshWaiter) {
  refreshWaiters.push(waiter)
}

function onTokenRefreshed(token: string) {
  refreshWaiters.forEach(w => {
    try {
      w.resolve(token)
    } catch {
      /* ignore */
    }
  })
  refreshWaiters.length = 0
}

function onRefreshFailed(err: unknown) {
  refreshWaiters.forEach(w => w.reject(err))
  refreshWaiters.length = 0
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
  response => {
    const contentType = String(response.headers?.['content-type'] ?? '').toLowerCase()
    const requestUrl = String(response.config?.url ?? '')
    if (contentType.includes('text/html') && requestUrl.startsWith('/')) {
      throw new Error(
        'API request returned HTML instead of JSON. This usually means production API base URL is misconfigured or routing is sending /api/* to the frontend app.',
      )
    }
    return response
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      const store = await loadAuthStore()

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          subscribeTokenRefresh({
            resolve: (token: string) => {
              if (originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${token}`
              }
              resolve(apiClient(originalRequest))
            },
            reject,
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
      } catch (refreshErr) {
        isRefreshing = false
        onRefreshFailed(refreshErr)
        store.getState().logout()
        window.location.href = '/login'
        return Promise.reject(error)
      }
    }

    const status = error.response?.status
    if (status === 502 || status === 503 || status === 504) {
      return Promise.reject(
        new Error(
          'The API is temporarily unreachable (bad gateway). This is usually a deployment or connection issue — try again in a minute. If it persists, confirm the backend service is healthy.',
        ),
      )
    }
    const message = (error.response?.data as any)?.detail || error.message
    return Promise.reject(new Error(message))
  }
)

export default apiClient
