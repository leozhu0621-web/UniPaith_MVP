import { useParams, Navigate } from 'react-router-dom'
import InstitutionDetail from './institution/InstitutionDetail'

/**
 * Authenticated School Detail (Spec 12) — `/s/institutions/:institutionId`.
 * Thin wrapper around the shared InstitutionDetail view (consolidated with the
 * public surface per Spec 12 §5 / gap G-S9).
 */
export default function InstitutionDetailPage() {
  const { institutionId } = useParams<{ institutionId: string }>()
  if (!institutionId) return <Navigate to="/s/explore" replace />
  return <InstitutionDetail institutionId={institutionId} isAuthenticated />
}
