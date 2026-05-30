import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth-store'

interface Props {
  role: 'student' | 'institution_admin'
  children: React.ReactNode
}

export default function RequireAuth({ role, children }: Props) {
  const { isAuthenticated, isLoading, user } = useAuthStore()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
      </div>
    )
  }

  // Not signed in — bounce to login, preserving where they were headed so we
  // can send them back after auth (Spec/04 §9, §15).
  if (!isAuthenticated) {
    const next = encodeURIComponent(location.pathname + location.search)
    return <Navigate to={`/login?next=${next}`} replace />
  }

  // Signed in as the wrong role — send to that role's home (Spec/04 §3).
  if (user?.role !== role) {
    const target = user?.role === 'student' ? '/s' : '/i/dashboard'
    return <Navigate to={target} replace />
  }

  return <>{children}</>
}
