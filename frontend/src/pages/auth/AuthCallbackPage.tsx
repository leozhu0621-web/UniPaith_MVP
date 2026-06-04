import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth-store'

export default function AuthCallbackPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [error, setError] = useState('')
  const googleCallback = useAuthStore(s => s.googleCallback)
  // StrictMode (React 18) mounts effects twice in dev; OAuth codes are
  // single-use, so a second exchange always fails. Latch to fire exactly once.
  const exchangeStarted = useRef(false)

  useEffect(() => {
    if (exchangeStarted.current) return
    exchangeStarted.current = true

    const code = searchParams.get('code')
    const state = searchParams.get('state') || ''

    if (!code) {
      setError('No authorization code received')
      return
    }

    // Extract role from state parameter (e.g. "role:institution_admin").
    // Whitelist client-side: state is attacker-influenceable, so only allow
    // the two known roles and default to 'student'.
    let role = 'student'
    if (state.startsWith('role:')) {
      const candidate = state.slice(5)
      if (candidate === 'student' || candidate === 'institution_admin') {
        role = candidate
      }
    }

    const redirectUri = `${window.location.origin}/auth/callback`

    googleCallback(code, redirectUri, role)
      .then(() => {
        const user = useAuthStore.getState().user
        // New students go to onboarding; returning students go to dashboard
        const isNewStudent = user?.role === 'student' &&
          new Date(user.created_at).getTime() > Date.now() - 60_000 // created within last minute
        const dest = isNewStudent ? '/onboarding'
          : user?.role === 'student' ? '/s'
          : '/i/dashboard'
        navigate(dest, { replace: true })
      })
      .catch((err) => {
        setError(err.message || 'Google sign-in failed')
      })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  if (error) {
    return (
      <div className="min-h-screen bg-muted flex items-center justify-center p-4">
        <div className="w-full max-w-md text-center">
          <h1 className="text-2xl font-bold mb-4">Sign-in failed</h1>
          <div className="bg-error-soft border border-error/30 text-error text-sm px-4 py-3 rounded mb-4">
            {error}
          </div>
          <Link to="/login" className="text-sm text-muted-foreground hover:underline">
            Back to login
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-muted flex items-center justify-center p-4">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-foreground mx-auto mb-4" />
        <p className="text-sm text-muted-foreground">Signing you in...</p>
      </div>
    </div>
  )
}
