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
  response => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }
    // #region agent log
    fetch('http://127.0.0.1:7640/ingest/56780e01-d332-4ae8-8f9d-c88718bcdca2',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'65023e'},body:JSON.stringify({sessionId:'65023e',runId:'initial',hypothesisId:'H3',location:'frontend/src/api/client.ts:response:error',message:'Axios response interceptor caught error',data:{status:error.response?.status??null,url:originalRequest?.url??null,method:originalRequest?.method??null,hasRetry:Boolean(originalRequest?._retry)},timestamp:Date.now()})}).catch(()=>{});
    // #endregion

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
        // #region agent log
        fetch('http://127.0.0.1:7640/ingest/56780e01-d332-4ae8-8f9d-c88718bcdca2',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'65023e'},body:JSON.stringify({sessionId:'65023e',runId:'initial',hypothesisId:'H3',location:'frontend/src/api/client.ts:response:refresh-success',message:'Token refresh succeeded during interceptor retry',data:{url:originalRequest?.url??null},timestamp:Date.now()})}).catch(()=>{});
        // #endregion
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`
        }
        return apiClient(originalRequest)
      } catch (refreshErr) {
        isRefreshing = false
        onRefreshFailed(refreshErr)
        // #region agent log
        fetch('http://127.0.0.1:7640/ingest/56780e01-d332-4ae8-8f9d-c88718bcdca2',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'65023e'},body:JSON.stringify({sessionId:'65023e',runId:'initial',hypothesisId:'H3',location:'frontend/src/api/client.ts:response:refresh-failed',message:'Token refresh failed and user will be logged out',data:{url:originalRequest?.url??null,refreshErrorMessage:refreshErr instanceof Error?refreshErr.message:'unknown'},timestamp:Date.now()})}).catch(()=>{});
        // #endregion
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
