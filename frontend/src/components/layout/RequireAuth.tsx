import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth-store'
import NoAccessPage from '../../pages/system/NoAccessPage'

interface Props {
  role: 'student' | 'institution_admin'
  children: React.ReactNode
}

export default function RequireAuth({ role, children }: Props) {
  const { isAuthenticated, isLoading, user } = useAuthStore()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  if (!isAuthenticated) {
    const next = encodeURIComponent(`${location.pathname}${location.search}`)
    return <Navigate to={`/login?next=${next}`} replace />
  }

  if (user?.role !== role) {
    // Spec 78 §5 — explicit 403 instead of a silent redirect to the user's own
    // home, so a wrong-role visit reads as "no access" rather than a confusing bounce.
    return <NoAccessPage />
  }

  return <>{children}</>
}
