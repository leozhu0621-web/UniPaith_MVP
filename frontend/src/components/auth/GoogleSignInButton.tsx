import { useEffect, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth-store'
import { showToast } from '../../stores/toast-store'
import { postLoginDestination } from '../../utils/auth-redirect'

const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined
const GIS_SRC = 'https://accounts.google.com/gsi/client'

declare global {
  interface Window {
    // Google Identity Services global (loaded on demand).
    google?: { accounts?: { id?: Record<string, (...args: unknown[]) => void> } }
  }
}

function loadGis(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (window.google?.accounts?.id) return resolve()
    const existing = document.querySelector<HTMLScriptElement>(`script[src="${GIS_SRC}"]`)
    if (existing) {
      existing.addEventListener('load', () => resolve())
      existing.addEventListener('error', () => reject(new Error('GIS failed to load')))
      return
    }
    const s = document.createElement('script')
    s.src = GIS_SRC
    s.async = true
    s.defer = true
    s.onload = () => resolve()
    s.onerror = () => reject(new Error('GIS failed to load'))
    document.head.appendChild(s)
  })
}

// "Sign in with Google" (GIS-direct). Renders only when VITE_GOOGLE_CLIENT_ID is
// configured — otherwise nothing, so email/password demo login still works.
export default function GoogleSignInButton() {
  const ref = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const googleLogin = useAuthStore(s => s.googleLogin)

  useEffect(() => {
    if (!CLIENT_ID || !ref.current) return
    let cancelled = false
    loadGis()
      .then(() => {
        const id = window.google?.accounts?.id
        if (cancelled || !id || !ref.current) return
        id.initialize({
          client_id: CLIENT_ID,
          callback: async (resp: { credential?: string }) => {
            if (!resp.credential) return
            try {
              await googleLogin(resp.credential)
              const user = useAuthStore.getState().user
              navigate(postLoginDestination(user?.role, searchParams))
            } catch {
              showToast('Google sign-in failed. Please try again.', 'error')
            }
          },
        })
        id.renderButton(ref.current, { theme: 'outline', size: 'large', text: 'continue_with' })
      })
      .catch(() => {
        /* GIS unavailable (offline / blocked) — silently fall back to email login. */
      })
    return () => {
      cancelled = true
    }
  }, [googleLogin, navigate, searchParams])

  if (!CLIENT_ID) return null

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3 text-xs text-muted-foreground">
        <span className="h-px flex-1 bg-border" /> or <span className="h-px flex-1 bg-border" />
      </div>
      <div className="flex justify-center">
        <div ref={ref} />
      </div>
    </div>
  )
}
