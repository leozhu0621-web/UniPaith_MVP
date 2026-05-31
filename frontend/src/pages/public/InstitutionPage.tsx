import { useEffect } from 'react'
import { useParams, useSearchParams, Navigate } from 'react-router-dom'
import { recordCampaignAction } from '../../api/institutions'
import InstitutionDetail from '../student/institution/InstitutionDetail'

/**
 * Public School Detail (Spec 12) — `/school/:institutionId`. Renders the same
 * InstitutionDetail view as the authenticated surface with `isAuthenticated`
 * false, so save/RSVP actions become sign-in CTAs (Spec 12 §5 / gap G-S9).
 * PublicLayout supplies the top nav; this wrapper only preserves campaign
 * attribution tracking for marketing deep-links (?cid=).
 */
export default function InstitutionPage() {
  const { institutionId } = useParams<{ institutionId: string }>()
  const [searchParams] = useSearchParams()

  useEffect(() => {
    const cid = searchParams.get('cid')
    if (cid && institutionId) {
      recordCampaignAction({ campaign_id: cid, action_type: 'view', target_id: institutionId }).catch(() => {})
    }
  }, [searchParams, institutionId])

  if (!institutionId) return <Navigate to="/browse" replace />
  return <InstitutionDetail institutionId={institutionId} isAuthenticated={false} />
}
