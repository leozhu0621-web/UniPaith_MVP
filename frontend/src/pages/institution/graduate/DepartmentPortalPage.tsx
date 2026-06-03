import { useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Heart, Users } from 'lucide-react'
import {
  getDepartmentDashboard,
  getDepartmentReview,
  type ReviewApplicant,
} from '../../../api/graduate'
import Card from '../../../components/ui/Card'
import Badge from '../../../components/ui/Badge'
import Tabs from '../../../components/ui/Tabs'
import Skeleton from '../../../components/ui/Skeleton'
import EmptyState from '../../../components/ui/EmptyState'
import { CENTRAL_STATUS_LABEL, DECISION_LABELS, fmtMoney } from './constants'
import FacultyRoster from './FacultyRoster'
import FundingPoolsPanel from './FundingPoolsPanel'

const DECISION_BADGE: Record<string, 'success' | 'info' | 'warning' | 'danger' | 'neutral'> = {
  admitted: 'success',
  conditional_admission: 'info',
  waitlisted: 'warning',
  rejected: 'danger',
  deferred: 'neutral',
}

function Kpi({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <div className="rounded-lg border border-border bg-background px-4 py-3">
      <div className="text-2xl font-semibold tabular-nums text-foreground">{value}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
      {hint && <div className="mt-0.5 text-[11px] text-muted-foreground">{hint}</div>}
    </div>
  )
}

function ApplicantRow({ a }: { a: ReviewApplicant }) {
  return (
    <Link
      to={`/i/admissions/applicant/${a.application_id}?tab=advisor-match`}
      className="flex items-center justify-between gap-3 rounded-lg border border-border bg-background p-3 transition-colors hover:border-secondary/40"
    >
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-medium text-foreground">{a.program_name}</span>
          {a.mutual_interest_count > 0 && (
            <Badge variant="info">
              <Heart size={11} /> {a.mutual_interest_count} mutual
            </Badge>
          )}
        </div>
        <div className="mt-1 text-xs text-muted-foreground">
          {a.status ?? 'submitted'}
          {a.decision && ` · ${DECISION_LABELS[a.decision as keyof typeof DECISION_LABELS] ?? a.decision}`}
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {a.recommended_decision && (
          <Badge variant={DECISION_BADGE[a.recommended_decision] ?? 'neutral'}>
            {DECISION_LABELS[a.recommended_decision]}
          </Badge>
        )}
        {a.central_status && (
          <Badge variant={a.central_status === 'pending' ? 'warning' : 'success'}>
            {a.central_status === 'pending' ? 'Awaiting central' : CENTRAL_STATUS_LABEL[a.central_status]}
          </Badge>
        )}
      </div>
    </Link>
  )
}

type DeptTab = 'applicants' | 'faculty' | 'funding'

const TABS = [
  { id: 'applicants', label: 'Applicants' },
  { id: 'faculty', label: 'Faculty' },
  { id: 'funding', label: 'Funding' },
]

export default function DepartmentPortalPage() {
  const { deptId } = useParams<{ deptId: string }>()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [tab, setTab] = useState<DeptTab>((searchParams.get('tab') as DeptTab) || 'applicants')

  const dashQ = useQuery({
    queryKey: ['dept-dashboard', deptId],
    queryFn: () => getDepartmentDashboard(deptId!),
    enabled: !!deptId,
  })
  const reviewQ = useQuery({
    queryKey: ['dept-review', deptId],
    queryFn: () => getDepartmentReview(deptId!),
    enabled: !!deptId && tab === 'applicants',
  })

  const handleTab = (t: string) => {
    setTab(t as DeptTab)
    setSearchParams({ tab: t })
  }

  if (dashQ.isLoading) return <div className="p-6"><Skeleton className="h-96" /></div>
  if (dashQ.isError || !dashQ.data)
    return (
      <div className="p-6">
        <EmptyState
          icon={<Users size={28} />}
          title="Department not found"
          description="This department may have been removed."
        />
      </div>
    )

  const dash = dashQ.data
  const dept = dash.department
  const deptOptions = [{ id: dept.id, name: dept.name }]

  return (
    <div className="mx-auto max-w-6xl space-y-5 p-6">
      <button
        type="button"
        onClick={() => navigate('/i/admissions?tab=graduate')}
        className="flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-secondary"
      >
        <ArrowLeft size={14} /> Graduate admissions
      </button>

      <header>
        <div className="flex items-center gap-2">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">{dept.name}</h1>
          {dept.code && (
            <span className="rounded bg-muted px-2 py-0.5 text-xs text-muted-foreground">
              {dept.code}
            </span>
          )}
        </div>
        {dept.description && <p className="mt-1 text-sm text-muted-foreground">{dept.description}</p>}
      </header>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Kpi label="Applicants" value={dash.applicant_count} />
        <Kpi label="Pending central" value={dash.recommended_count} />
        <Kpi label="Admitted" value={dash.admitted_count} hint={`${dash.yield.accepted} accepted`} />
        <Kpi
          label="Funding committed"
          value={fmtMoney(dash.funding.total_committed)}
          hint={`of ${fmtMoney(dash.funding.total_budget)}`}
        />
      </div>

      <Tabs tabs={TABS} activeTab={tab} onChange={handleTab} />

      {tab === 'applicants' && (
        <Card className="p-5">
          {reviewQ.isLoading ? (
            <Skeleton className="h-40" />
          ) : !reviewQ.data || reviewQ.data.applicants.length === 0 ? (
            <EmptyState
              icon={<Users size={28} />}
              title="No applicants yet"
              description="Applicants to this department's programs appear here for scoped review and recommendation."
            />
          ) : (
            <div className="space-y-2.5">
              {reviewQ.data.applicants.map(a => (
                <ApplicantRow key={a.application_id} a={a} />
              ))}
            </div>
          )}
        </Card>
      )}

      {tab === 'faculty' && <FacultyRoster departmentId={dept.id} departments={deptOptions} />}

      {tab === 'funding' && <FundingPoolsPanel departmentId={dept.id} departments={deptOptions} />}
    </div>
  )
}
