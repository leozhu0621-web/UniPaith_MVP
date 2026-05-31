import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { listMyApplications } from '../../api/applications'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import EmptyState from '../../components/ui/EmptyState'
import Select from '../../components/ui/Select'
import { SkeletonCard } from '../../components/ui/Skeleton'
import { formatDate } from '../../utils/format'
import { STATUS_COLORS } from '../../utils/constants'
import { FileText, Star, ChevronRight } from 'lucide-react'
import CounselorNudge from './components/CounselorNudge'
import type { Application } from '../../types'

function bucket(app: Application) {
  if (app.status === 'submitted') return 'submitted'
  if (app.status === 'under_review') return 'under_review'
  if (app.status === 'decision_made') return 'decided'
  if (app.status !== 'draft') return 'in_progress'
  if (app.ready_to_submit || (app.readiness_pct ?? 0) >= 100) return 'ready'
  if ((app.readiness_pct ?? 0) > 0) return 'in_progress'
  return 'not_started'
}

export default function ApplicationsPage() {
  const navigate = useNavigate()
  const [statusFilter, setStatusFilter] = useState('all')
  const [sortBy, setSortBy] = useState('deadline')

  const { data: applications, isLoading } = useQuery({
    queryKey: ['my-applications'],
    queryFn: listMyApplications,
  })
  const list: Application[] = Array.isArray(applications) ? applications : []

  const counts = useMemo(() => {
    const c = { not_started: 0, in_progress: 0, ready: 0, submitted: 0, under_review: 0, decided: 0 }
    for (const a of list) c[bucket(a) as keyof typeof c] += 1
    return c
  }, [list])

  const nextActions = useMemo(
    () =>
      list
        .filter(a => a.status === 'draft' && (a.ready_to_submit || a.next_action))
        .slice(0, 3),
    [list],
  )

  const filtered = useMemo(() => {
    let rows = [...list]
    if (statusFilter === 'ready') {
      rows = rows.filter(a => a.status === 'draft' && bucket(a) === 'ready')
    } else if (statusFilter !== 'all') {
      rows = rows.filter(a => a.status === statusFilter)
    }
    rows.sort((a, b) => {
      if (sortBy === 'readiness') return (b.readiness_pct ?? 0) - (a.readiness_pct ?? 0)
      const da = a.program?.application_deadline
        ? new Date(a.program.application_deadline).getTime()
        : Infinity
      const db = b.program?.application_deadline
        ? new Date(b.program.application_deadline).getTime()
        : Infinity
      return da - db
    })
    return rows
  }, [list, statusFilter, sortBy])

  if (isLoading) {
    return (
      <div className="p-6 space-y-4 max-w-3xl mx-auto">
        {Array.from({ length: 3 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    )
  }

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-semibold text-student-ink">Your portfolio</h1>
      <p className="text-sm text-student-text mt-1 mb-4">
        Not started {counts.not_started} · In progress {counts.in_progress} · Ready to submit{' '}
        {counts.ready} · Submitted {counts.submitted} · Under review {counts.under_review} ·
        Decided {counts.decided}
      </p>

      {list.length === 0 && (
        <CounselorNudge
          message="No applications yet. Start one from your Saved list or Match."
          actionLabel="Explore programs"
          actionTo="/s/explore"
        />
      )}

      {nextActions.length > 0 && (
        <Card className="p-4 mb-4">
          <p className="text-xs font-semibold uppercase mb-2">Next actions</p>
          {nextActions.map(app => (
            <button
              key={app.id}
              type="button"
              className="block w-full text-left text-sm py-1 hover:opacity-80"
              onClick={() => navigate(`/s/applications/${app.id}`)}
            >
              <Star size={12} className="inline text-[hsl(var(--primary))] mr-1" />
              {app.program?.program_name} — {app.ready_to_submit ? 'Ready now' : app.next_action}
            </button>
          ))}
        </Card>
      )}

      <div className="flex gap-3 mb-4">
        <Select
          label="Filter"
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          options={[
            { value: 'all', label: 'All' },
            { value: 'draft', label: 'Draft' },
            { value: 'ready', label: 'Ready to submit' },
            { value: 'submitted', label: 'Submitted' },
            { value: 'under_review', label: 'Under review' },
            { value: 'decision_made', label: 'Decided' },
          ]}
        />
        <Select
          label="Sort"
          value={sortBy}
          onChange={e => setSortBy(e.target.value)}
          options={[
            { value: 'deadline', label: 'Deadline' },
            { value: 'readiness', label: 'Readiness %' },
          ]}
        />
      </div>

      <div className="space-y-3">
        {filtered.length === 0 ? (
          <EmptyState
            icon={<FileText size={48} />}
            title="No applications yet"
            description="Start one from your Saved list or Match."
            action={{ label: 'Explore programs', onClick: () => navigate('/s/explore') }}
          />
        ) : (
          filtered.map(app => (
            <Card
              key={app.id}
              className="p-4 cursor-pointer hover:shadow-sm"
              onClick={() => navigate(`/s/applications/${app.id}`)}
            >
              <p className="font-semibold text-sm">{app.program?.program_name}</p>
              <p className="text-xs text-student-text">
                {app.program?.institution_name}
              </p>
              <p className="text-sm mt-2">
                Status: In progress ({app.readiness_pct ?? 0}%)
              </p>
              {app.next_action && (
                <p className="text-xs text-muted-foreground">Next: {app.next_action}</p>
              )}
              <div className="flex gap-2 mt-2">
                <Badge variant={(STATUS_COLORS[app.status] || 'neutral') as 'neutral'}>
                  {app.status.replace(/_/g, ' ')}
                </Badge>
              </div>
              <span className="text-xs text-[hsl(var(--accent))] mt-2 inline-flex items-center">
                Open application <ChevronRight size={12} />
              </span>
            </Card>
          ))
        )}
      </div>
    </div>
  )
}
