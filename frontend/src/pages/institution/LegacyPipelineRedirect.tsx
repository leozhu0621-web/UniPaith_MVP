import { Navigate, useParams, useSearchParams } from 'react-router-dom'
import { admissionsUrl, applicantUrl, type PipelineView } from '../../utils/institution-routes'

const PIPELINE_VIEWS: PipelineView[] = ['board', 'list', 'review', 'priority']

/** Legacy `/i/pipeline` → Spec 31 `/i/admissions?tab=pipeline&view=…` */
export function LegacyPipelineRedirect() {
  const [searchParams] = useSearchParams()
  const raw = searchParams.get('tab') || 'board'
  const view: PipelineView = PIPELINE_VIEWS.includes(raw as PipelineView) ? (raw as PipelineView) : 'board'
  return <Navigate to={admissionsUrl('pipeline', view)} replace />
}

/** Legacy `/i/pipeline/:id` → `/i/admissions/applicant/:id` */
export function LegacyApplicantRedirect() {
  const { studentId } = useParams<{ studentId: string }>()
  const [searchParams] = useSearchParams()
  const detailTab = searchParams.get('tab') ?? undefined
  if (!studentId) return <Navigate to={admissionsUrl('pipeline', 'board')} replace />
  return <Navigate to={applicantUrl(studentId, detailTab)} replace />
}
