/**
 * My Space › Prep › Readiness strip (Spec 2026-06-18 §1) — a compact answer to
 * "am I application-ready?" sitting above the five disconnected Prep tabs. It
 * composes data the room already loads (shared query keys → cache dedupes) into
 * four deep-linking cells: Recommenders · Interviews · Documents · Workshops.
 *
 * Voice: name the noun, count the real thing, no manufactured cheer. Warning
 * tone (--warning) flags an open loop (a recommender still out, an interview
 * awaiting a response). Gold stays reserved for earned milestones.
 */
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { listRecommendations } from '../../../../api/recommendations'
import { getMyInterviews } from '../../../../api/interviews'
import { listDocuments } from '../../../../api/documents'
import { listWorkshopRuns } from '../../../../api/workshops-feedback'
import type { Interview } from '../../../../types'

// Mirror InterviewsTab's "needs a response" bucket exactly so the count here
// can never drift from what the tab shows. (InterviewsTab keeps RESPOND_STATUSES
// local, so we replicate the same set rather than importing it.)
const RESPOND_STATUSES = new Set(['proposed', 'reschedule_requested'])

interface CellProps {
  label: string
  value: React.ReactNode
  tone?: 'default' | 'warning'
  onClick: () => void
}

function ReadinessCell({ label, value, tone = 'default', onClick }: CellProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="min-w-0 rounded-lg bg-muted p-3 text-left transition-colors hover:bg-border/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-secondary"
    >
      <p
        className={`text-lg font-semibold leading-none ${
          tone === 'warning' ? 'text-warning' : 'text-foreground'
        }`}
      >
        {value}
      </p>
      <p className="mt-1 truncate text-eyebrow uppercase text-muted-foreground">{label}</p>
    </button>
  )
}

export default function PrepReadiness() {
  const navigate = useNavigate()

  const recsQ = useQuery({ queryKey: ['recommendations'], queryFn: listRecommendations })
  const interviewsQ = useQuery({ queryKey: ['interviews', 'prep'], queryFn: getMyInterviews })
  const docsQ = useQuery({ queryKey: ['documents'], queryFn: listDocuments })
  // Wrap so the query context isn't passed as `listWorkshopRuns`'s `domain` arg.
  const runsQ = useQuery({ queryKey: ['workshop-runs', 'prep'], queryFn: () => listWorkshopRuns() })

  const loading =
    recsQ.isLoading || interviewsQ.isLoading || docsQ.isLoading || runsQ.isLoading

  // Slim skeleton row while the four core queries load.
  if (loading) {
    return (
      <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
        {[0, 1, 2, 3].map(i => (
          <div key={i} className="h-[58px] animate-pulse rounded-lg bg-muted" />
        ))}
      </div>
    )
  }

  const recs = recsQ.data ?? []
  const interviews: Interview[] = interviewsQ.data ?? []
  const docs = docsQ.data ?? []
  const runs = runsQ.data ?? []

  // Cold start: nothing prepared anywhere — let each tab own its empty state
  // rather than show a meaningless 0/0/0/0 strip.
  if (recs.length === 0 && interviews.length === 0 && docs.length === 0 && runs.length === 0) {
    return null
  }

  // Recommenders — received over total ever asked. A letter is "in flight" once
  // asked ('requested') or while the recommender works on it ('submitted'); only
  // 'received' closes the loop. 'draft' hasn't been sent, so it doesn't count.
  const recWaiting = recs.filter(
    (r: { status?: string }) => r.status === 'requested' || r.status === 'submitted',
  ).length
  const recReceived = recs.filter((r: { status?: string }) => r.status === 'received').length
  const recTotal = recWaiting + recReceived

  // Interviews — the "needs a response" bucket (matches InterviewsTab).
  const needResponse = interviews.filter(
    iv => RESPOND_STATUSES.has(String(iv.status)) && !iv.async_expired,
  ).length

  return (
    <div className="mt-3">
      <p className="mb-1.5 text-eyebrow uppercase text-muted-foreground">Application readiness</p>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <ReadinessCell
          label="Recommenders"
          value={`${recReceived}/${recTotal} received`}
          tone={recWaiting > 0 ? 'warning' : 'default'}
          onClick={() => navigate('/s/prep?tab=recommenders')}
        />
        <ReadinessCell
          label="Interviews"
          value={needResponse > 0 ? `${needResponse} need a response` : 'All responded'}
          tone={needResponse > 0 ? 'warning' : 'default'}
          onClick={() => navigate('/s/prep?tab=interviews')}
        />
        <ReadinessCell
          label="Documents"
          value={`${docs.length} on file`}
          onClick={() => navigate('/s/prep?tab=documents')}
        />
        <ReadinessCell
          label="Workshops"
          value={`${runs.length} feedback run${runs.length === 1 ? '' : 's'}`}
          onClick={() => navigate('/s/prep?tab=workshops')}
        />
      </div>
    </div>
  )
}
