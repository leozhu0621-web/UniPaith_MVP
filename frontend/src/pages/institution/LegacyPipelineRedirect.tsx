import { Navigate, useParams, useSearchParams } from 'react-router-dom'
import { admissionsUrl, applicantUrl } from '../../utils/institution-routes'

/** Legacy `/i/pipeline` → Spec 31 `/i/admissions?tab=pipeline&view=…` */
export function LegacyPipelineRedirect() {
  const [searchParams] = useSearchParams()
  const view = searchParams.get('tab') || 'board'
  return <Navigate to={admissionsUrl('pipeline', view as 'board')} replace />
}

/** Legacy `/i/pipeline/:id` → `/i/admissions/applicant/:id` */
export function LegacyApplicantRedirect() {
  const { studentId } = useParams<{ studentId: string }>()
  const [searchParams] = useSearchParams()
  const detailTab = searchParams.get('tab') ?? undefined
  if (!studentId) return <Navigate to={admissionsUrl('pipeline', 'board')} replace />
  return <Navigate to={applicantUrl(studentId, detailTab)} replace />
}
