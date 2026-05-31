import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth-store'
import { roleDefaultPath } from '../../utils/auth-redirect'

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
    return <Navigate to={roleDefaultPath(user?.role)} replace />
  }

  return <>{children}</>
}
