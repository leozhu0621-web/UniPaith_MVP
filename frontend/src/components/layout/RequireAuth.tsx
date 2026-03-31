import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/auth-store'

interface Props {
  role: 'student' | 'institution_admin'
  children: React.ReactNode
}

export default function RequireAuth({ role, children }: Props) {
  const { isAuthenticated, isLoading, user } = useAuthStore()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (user?.role !== role) {
    const target = user?.role === 'student' ? '/s/chat' : '/i/dashboard'
    return <Navigate to={target} replace />
  }

  return <>{children}</>
}
