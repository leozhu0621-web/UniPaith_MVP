import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth-store'

export default function AuthCallbackPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [error, setError] = useState('')
  const googleCallback = useAuthStore(s => s.googleCallback)

  useEffect(() => {
    const code = searchParams.get('code')
    const state = searchParams.get('state') || ''

    if (!code) {
      setError('No authorization code received')
      return
    }

    // Extract role from state parameter (e.g. "role:institution_admin")
    let role = 'student'
    if (state.startsWith('role:')) {
      role = state.slice(5)
    }

    const redirectUri = `${window.location.origin}/auth/callback`

    googleCallback(code, redirectUri, role)
      .then(() => {
        const user = useAuthStore.getState().user
        // New students go to onboarding; returning students go to dashboard
        const isNewStudent = user?.role === 'student' &&
          new Date(user.created_at).getTime() > Date.now() - 60_000 // created within last minute
        const dest = user?.role === 'admin' ? '/admin'
          : isNewStudent ? '/onboarding'
          : user?.role === 'student' ? '/s/dashboard'
          : '/i/dashboard'
        navigate(dest, { replace: true })
      })
      .catch((err) => {
        setError(err.message || 'Google sign-in failed')
      })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="w-full max-w-md text-center">
          <h1 className="text-2xl font-bold mb-4">Sign-in failed</h1>
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded mb-4">
            {error}
          </div>
          <a href="/login" className="text-sm text-gray-600 hover:underline">
            Back to login
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto mb-4" />
        <p className="text-sm text-gray-500">Signing you in...</p>
      </div>
    </div>
  )
}
