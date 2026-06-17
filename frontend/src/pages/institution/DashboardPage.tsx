import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  Plus,
  GitBranch,
  ClipboardCheck,
  Bell,
  BookOpen,
  Calendar,
  Users,
  TrendingUp,
  Target,
  Mail,
  Brain,
  Shield,
  Zap,
  MessageSquare,
  Inbox,
  ArrowRight,
} from 'lucide-react'
import { getInstitution, getInstitutionPrograms, getDashboardSummary, getIntelligenceDigest, getYieldRiskAlerts } from '../../api/institutions'
import { getReviewPriorityQueue, getIntegritySignals } from '../../api/reviews'
import { getNotifications, getUnreadCount } from '../../api/notifications'
import { admissionsUrl, applicantUrl, INQUIRIES_URL } from '../../utils/institution-routes'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Skeleton from '../../components/ui/Skeleton'
import EmptyState from '../../components/ui/EmptyState'
import Table from '../../components/ui/Table'
import QueryError from '../../components/ui/QueryError'
import FairnessPanel from './fairness/FairnessPanel'
import { formatDate, formatRelative, formatCurrency, formatPercent } from '../../utils/format'
import { DEGREE_LABELS } from '../../utils/constants'
import type { Notification, PrioritizedApplication, IntegritySignal, Program, DashboardSummary } from '../../types'

const INTEGRITY_LINE: Record<string, (n: number) => string> = {
  essay_authenticity: (n) => `${n} essay authenticity flag${n === 1 ? '' : 's'} pending review`,
  duplicate_submission: (n) => `${n} duplicate-account suspicion${n === 1 ? '' : 's'}`,
  credential_mismatch: (n) => `${n} credential mismatch flag${n === 1 ? '' : 's'}`,
  incomplete_profile: (n) => `${n} incomplete profile flag${n === 1 ? '' : 's'}`,
}
function integrityLine(type: string, count: number): string {
  return (INTEGRITY_LINE[type] ?? ((n) => `${n} ${type.replace(/_/g, ' ')} flag${n === 1 ? '' : 's'} pending review`))(count)
}

// Short noun labels for the per-type breakdown chips — the full sentence above
// is kept as each chip's title for the count-in-context reading.
const INTEGRITY_CHIP_LABEL: Record<string, string> = {
  essay_authenticity: 'Essay authenticity',
  duplicate_submission: 'Duplicate',
  credential_mismatch: 'Credential mismatch',
  incomplete_profile: 'Incomplete profile',
}

export default function DashboardPage() {
  const navigate = useNavigate()

  const institutionQ = useQuery({ queryKey: ['institution'], queryFn: getInstitution, retry: false })
  const programsQ = useQuery({ queryKey: ['institution-programs'], queryFn: getInstitutionPrograms })
  const summaryQ = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: getDashboardSummary,
    enabled: !!institutionQ.data,
  })
  const notificationsQ = useQuery({
    queryKey: ['notifications', { limit: 10 }],
    queryFn: () => getNotifications({ limit: 10 }),
  })

  const priorityQ = useQuery({
    queryKey: ['dashboard-priority'],
    queryFn: () => getReviewPriorityQueue(),
    enabled: !!institutionQ.data,
  })
  const integrityQ = useQuery({
    queryKey: ['dashboard-integrity'],
    queryFn: () => getIntegritySignals(undefined, 'open'),
    enabled: !!institutionQ.data,
  })
  const unreadQ = useQuery({
    queryKey: ['notifications-unread-count'],
    queryFn: getUnreadCount,
    enabled: !!institutionQ.data,
  })
  const digestQ = useQuery({
    queryKey: ['intelligence-digest'],
    queryFn: getIntelligenceDigest,
    enabled: !!institutionQ.data,
    staleTime: 1000 * 60 * 30,
  })
  const yieldRiskQ = useQuery({
    queryKey: ['yield-risk-alerts'],
    queryFn: getYieldRiskAlerts,
    enabled: !!institutionQ.data,
    staleTime: 1000 * 60 * 15,
  })
  const institution = institutionQ.data
  const programs: Program[] = Array.isArray(programsQ.data) ? programsQ.data : []
  const summary: DashboardSummary | undefined = summaryQ.data
  const notifications: Notification[] = Array.isArray(notificationsQ.data) ? notificationsQ.data : []
  const topPriority: PrioritizedApplication[] = (Array.isArray(priorityQ.data) ? priorityQ.data : []).slice(0, 5)
  const openAlerts: IntegritySignal[] = Array.isArray(integrityQ.data) ? integrityQ.data : []
  const unreadNotifications: number = unreadQ.data?.count ?? unreadQ.data?.unread_count ?? 0
  const integrityBreakdown = useMemo(() => {
    const byType: Record<string, number> = {}
    for (const sig of openAlerts) {
      byType[sig.signal_type] = (byType[sig.signal_type] ?? 0) + 1
    }
    return Object.entries(byType).map(([type, count]) => ({ type, count, label: integrityLine(type, count) }))
  }, [openAlerts])

  const isLoading = institutionQ.isLoading || programsQ.isLoading

  if (isLoading) {
    return (
      <div className="space-y-6 p-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-28" />)}
        </div>
        <Skeleton className="h-64" />
      </div>
    )
  }

  if (institutionQ.isError) {
    return (
      <div className="p-6">
        <Card pad={false} className="p-8 text-center border-dashed border-2 border-border bg-muted/30">
          <LayoutDashboard size={48} className="mx-auto text-muted-foreground mb-4" />
          <h2 className="text-xl font-semibold text-foreground mb-2">No institution set up yet</h2>
          <p className="text-muted-foreground mb-6 max-w-md mx-auto">
            Create your first program so students can discover and apply to it.
          </p>
          <Button onClick={() => navigate('/i/programs')}>Create a program</Button>
        </Card>
      </div>
    )
  }

  if (!institution) return null

  // Spec 31 §2 — executive KPI row: Total apps · Conversion · Avg match · Yield (proj).
  const conversionVal = summary?.conversion_pct ?? summary?.acceptance_rate
  const projYieldVal = summary?.projected_yield_pct ?? summary?.yield_rate
  const executiveKpis = [
    {
      label: 'Total apps',
      value: summary?.total_applications ?? 0,
      icon: Users,
      color: 'text-muted-foreground bg-muted',
    },
    {
      label: 'Accept rate',
      value: conversionVal != null ? formatPercent(conversionVal) : '—',
      icon: Target,
      color: 'text-secondary bg-secondary/10',
    },
    {
      label: 'Avg match',
      value: summary?.avg_match != null ? summary.avg_match : '—',
      icon: Brain,
      color: 'text-muted-foreground bg-muted',
    },
    {
      label: 'Yield (proj)',
      value: projYieldVal != null ? formatPercent(projYieldVal) : '—',
      icon: TrendingUp,
      color: 'text-secondary bg-secondary/10',
    },
  ]
  const priorityQueue = summary?.priority_queue ?? []

  const operationalKpis = [
    {
      label: 'Programs Published',
      value: `${summary?.published_program_count ?? 0}/${summary?.program_count ?? programs.length}`,
      icon: BookOpen,
      color: 'text-secondary bg-secondary/10',
    },
    {
      label: 'Active Events',
      value: summary?.active_events_count ?? 0,
      icon: Calendar,
      color: 'text-warning bg-warning-soft',
    },
    {
      label: 'Unread Inbox',
      value: summary?.unread_messages_count ?? 0,
      icon: Mail,
      color: 'text-secondary bg-secondary/10',
    },
  ]
  const programColumns = [
    { key: 'program_name', label: 'Program' },
    {
      key: 'degree_type',
      label: 'Degree',
      render: (row: Program) => <Badge variant="info">{DEGREE_LABELS[row.degree_type] ?? row.degree_type}</Badge>,
    },
    {
      key: 'is_published',
      label: 'Status',
      render: (row: Program) => (
        <Badge variant={row.is_published ? 'success' : 'neutral'}>
          {row.is_published ? 'Published' : 'Draft'}
        </Badge>
      ),
    },
    {
      key: 'application_deadline',
      label: 'Deadline',
      render: (row: Program) => formatDate(row.application_deadline),
    },
    {
      key: 'tuition',
      label: 'Tuition',
      render: (row: Program) => formatCurrency(row.tuition),
    },
  ]

  return (
    <div className="space-y-6 p-6">
      <div>
        <p className="up-eyebrow mb-1">
          {institution.name}{summary?.cycle ? ` · ${summary.cycle} cycle` : ''}
        </p>
        <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Active-cycle intake — queues, integrity, inquiries, and yield.
        </p>
      </div>

      {/* Executive KPI row — Spec 31 §2 (Total apps · Conversion · Avg match · Yield proj). */}
      {summaryQ.isError && (
        <QueryError variant="inline" detail="We couldn't load your dashboard metrics — the figures below may be incomplete." onRetry={() => summaryQ.refetch()} />
      )}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-3">
        {executiveKpis.map(kpi => (
          <Card pad={false} key={kpi.label} className="p-5">
            <div className="flex items-center gap-3">
              <div className={`p-2.5 rounded-lg ${kpi.color}`}>
                <kpi.icon size={20} />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">{kpi.label}</p>
                <p className="text-3xl font-bold text-foreground">{kpi.value}</p>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Priority Queue — Spec 31 §2: categorized, actionable, with deep links. */}
      {priorityQueue.length > 0 && (
        <Card pad={false} className="p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-foreground">Priority Queue</h3>
            <Badge variant="info">{priorityQueue.length} to triage</Badge>
          </div>
          <div className="space-y-2">
            {priorityQueue.map(item => (
              <button
                key={item.category}
                onClick={() => navigate(item.deep_link)}
                className="flex w-full items-center justify-between gap-3 rounded-lg border border-border px-3 py-2 text-left transition-colors hover:bg-muted"
              >
                <span className="flex items-center gap-2 text-sm text-foreground">
                  <span className="inline-flex h-6 min-w-[1.5rem] items-center justify-center rounded px-1.5 text-xs font-bold bg-warning-soft text-warning">
                    {item.count}
                  </span>
                  {item.category}
                </span>
                <span className="flex items-center gap-1 text-xs font-medium text-secondary">
                  See all <ArrowRight size={13} />
                </span>
              </button>
            ))}
          </div>
        </Card>
      )}

      {/* Intelligence Digest — Spec 31 §2 */}
      {digestQ.isError && (
        <Card pad={false} className="p-4 border-border bg-card">
          <div className="flex items-center gap-2 mb-1">
            <Brain size={18} className="text-muted-foreground" />
            <h3 className="text-sm font-semibold text-foreground">Intelligence Digest</h3>
          </div>
          <QueryError variant="inline" detail="We couldn't load the intelligence digest." onRetry={() => digestQ.refetch()} />
        </Card>
      )}
      {digestQ.data?.digest && (
        <Card pad={false} className="p-4 border-border bg-card">
          <div className="flex items-center gap-2 mb-3">
            <Brain size={18} className="text-muted-foreground" />
            <h3 className="text-sm font-semibold text-foreground">Intelligence Digest</h3>
            <Badge variant="info">Auto-generated</Badge>
          </div>
          <div className="text-sm text-foreground leading-relaxed whitespace-pre-line">
            {digestQ.data.digest}
          </div>
          <p className="text-xs text-muted-foreground/70 mt-2">Generated {formatRelative(digestQ.data.generated_at)}</p>
        </Card>
      )}

      {/* Yield-Risk Alerts — Spec 31 §2 */}
      {yieldRiskQ.isError && (
        <Card pad={false} className="p-4 border-warning/30 bg-warning-soft/20">
          <div className="flex items-center gap-2 mb-1">
            <TrendingUp size={16} className="text-warning" />
            <h3 className="text-sm font-semibold text-foreground">Yield-Risk Alerts</h3>
          </div>
          <QueryError variant="inline" detail="We couldn't load yield-risk alerts." onRetry={() => yieldRiskQ.refetch()} />
        </Card>
      )}
      {(yieldRiskQ.data?.alerts?.length ?? 0) > 0 && (
        <Card pad={false} className="p-4 border-warning/30 bg-warning-soft/20">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp size={16} className="text-warning" />
            <h3 className="text-sm font-semibold text-foreground">Yield-Risk Alerts</h3>
            <Badge variant="warning">{yieldRiskQ.data!.count ?? yieldRiskQ.data!.alerts.length} at risk</Badge>
          </div>
          {yieldRiskQ.data!.alerts.length >= 3 && (
            <p className="text-sm text-foreground mb-2">
              {yieldRiskQ.data!.alerts.length} admitted students haven&apos;t responded
              {yieldRiskQ.data!.alerts[0]?.days_remaining != null && yieldRiskQ.data!.alerts[0].days_remaining >= 0
                ? `; deadline in ${yieldRiskQ.data!.alerts[0].days_remaining} days`
                : ''}
            </p>
          )}
          <div className="space-y-2">
            {yieldRiskQ.data!.alerts.slice(0, 5).map(alert => (
              <button
                key={alert.application_id}
                type="button"
                onClick={() => navigate(applicantUrl(alert.application_id, 'decision'))}
                className="w-full flex items-center justify-between gap-3 p-2 rounded-lg border border-border bg-background hover:bg-muted transition-colors text-left"
              >
                <div className="min-w-0">
                  <span className="text-sm font-medium text-foreground block truncate">
                    {alert.student_name ?? `Applicant ${alert.student_id.slice(0, 8)}`}
                  </span>
                  <span className="text-xs text-muted-foreground">{alert.reason}</span>
                </div>
                <Badge variant={alert.risk_level === 'high' ? 'danger' : 'warning'}>{alert.risk_level}</Badge>
              </button>
            ))}
          </div>
        </Card>
      )}

      {/* Integrity Signals + New Inquiries — Spec 31 §2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <Card pad={false} className={`p-4 ${openAlerts.length > 0 || integrityQ.isError ? 'border-warning/40' : ''}`}>
          <div className="flex items-center gap-2 mb-2">
            <Shield size={18} className={openAlerts.length > 0 || integrityQ.isError ? 'text-warning' : 'text-success'} />
            <h3 className="text-sm font-semibold text-foreground">Integrity Signals</h3>
          </div>
          {integrityQ.isError ? (
            <QueryError variant="inline" detail="We couldn't load integrity signals — this is not an all-clear." onRetry={() => integrityQ.refetch()} />
          ) : integrityBreakdown.length > 0 ? (
            <div className="flex flex-wrap gap-1.5 mb-3">
              {integrityBreakdown.map(row => (
                <button
                  key={row.type}
                  onClick={() => navigate(admissionsUrl('integrity', undefined, row.type))}
                  title={row.label}
                  className="inline-flex items-center gap-1.5 rounded-full border border-warning/30 bg-warning-soft/40 px-2.5 py-1 text-sm font-medium text-foreground hover:bg-warning-soft/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-secondary"
                >
                  <span className="text-warning" aria-hidden>⚠</span>
                  {INTEGRITY_CHIP_LABEL[row.type] ?? row.type.replace(/_/g, ' ')}
                  <span className="tabular-nums font-semibold text-warning">{row.count}</span>
                </button>
              ))}
            </div>
          ) : (
            <p className="text-sm text-success mb-2">All clear — no integrity issues</p>
          )}
          {!integrityQ.isError && (summary?.integrity_signals_count ?? openAlerts.length) > 0 && (
            <Button size="sm" variant="secondary" onClick={() => navigate(admissionsUrl('integrity'))} className="flex items-center gap-1">
              <Shield size={12} /> Review queue
            </Button>
          )}
        </Card>

        <Card pad={false} className={`p-4 ${(summary?.new_inquiries_24h ?? 0) > 0 ? 'border-secondary/30' : ''}`}>
          <div className="flex items-center gap-2 mb-2">
            <Inbox size={18} className={(summary?.new_inquiries_24h ?? 0) > 0 ? 'text-secondary' : 'text-muted-foreground'} />
            <h3 className="text-sm font-semibold text-foreground">New Inquiries</h3>
          </div>
          <p className="text-2xl font-bold text-foreground">
            Last 24h: {summary?.new_inquiries_24h ?? 0}
            {(summary?.unanswered_inquiries_4h ?? 0) > 0 && (
              <span className="text-base font-bold text-warning"> ({summary!.unanswered_inquiries_4h} unanswered ≥ 4h)</span>
            )}
          </p>
          <Button size="sm" variant="secondary" onClick={() => navigate(INQUIRIES_URL)} className="mt-2 flex items-center gap-1">
            <MessageSquare size={12} /> Open inquiry queue
          </Button>
        </Card>
      </div>

      {/* Fairness — Spec 46 §6 (G-I5 / G-D4): disparate-impact auto-halt panel.
          Supersedes the Spec 31 §11 advisory representation check with the
          authoritative halt-status surface (per-cohort signals + override link). */}
      <FairnessPanel />

      {/* AI Priority Queue Preview */}
      {priorityQ.isError && (
        <Card pad={false} className="p-4">
          <div className="flex items-center gap-2 mb-1">
            <Zap size={16} className="text-warning" />
            <h3 className="text-sm font-semibold text-foreground">Priority Review Queue</h3>
          </div>
          <QueryError variant="inline" detail="We couldn't load the priority review queue." onRetry={() => priorityQ.refetch()} />
        </Card>
      )}
      {topPriority.length > 0 && (
        <Card pad={false} className="p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Zap size={16} className="text-warning" />
              <h3 className="text-sm font-semibold text-foreground">Priority Review Queue</h3>
              <Badge variant="warning">{topPriority.length} urgent</Badge>
            </div>
            <Button size="sm" variant="ghost" onClick={() => navigate(admissionsUrl('pipeline', 'priority'))}>View All</Button>
          </div>
          <div className="space-y-1.5">
            {topPriority.map((p, i) => (
              <div key={p.application_id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted cursor-pointer" onClick={() => navigate(applicantUrl(p.application_id))}>
                <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-primary-foreground shrink-0 ${
                  p.priority_score >= 70 ? 'bg-error' : p.priority_score >= 40 ? 'bg-warning' : 'bg-success'
                }`}>
                  {Math.round(p.priority_score)}
                </div>
                <div className="flex-1 min-w-0">
                  <span className="text-sm text-foreground">#{i + 1} Applicant {p.student_id.slice(0, 8)}</span>
                  <span className="text-xs text-muted-foreground/70 ml-2">{p.program_name}</span>
                </div>
                <div className="flex gap-1">
                  {p.priority_reasons.slice(0, 2).map((r, j) => (
                    <span key={j} className="text-xs bg-muted text-muted-foreground px-1.5 py-0.5 rounded">{r}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Quick Actions */}
      <Card pad={false} className="p-4">
        <h3 className="text-sm font-semibold text-foreground mb-3">Quick Actions</h3>
        <div className="flex flex-wrap gap-2">
          <Button onClick={() => navigate('/i/programs/new')} className="flex items-center gap-2">
            <Plus size={16} /> Add Program
          </Button>
          <Button onClick={() => navigate(admissionsUrl('pipeline', 'review'))} variant="secondary" className="flex items-center gap-2">
            <ClipboardCheck size={16} /> Triage Review Queue
          </Button>
          <Button onClick={() => navigate(admissionsUrl('pipeline', 'board'))} variant="secondary" className="flex items-center gap-2">
            <GitBranch size={16} /> Applications Board
          </Button>
          <Button onClick={() => navigate('/i/campaigns')} variant="secondary" className="flex items-center gap-2">
            <Bell size={16} /> Launch Outreach
          </Button>
        </div>
      </Card>

      <div>
        <h3 className="text-sm font-semibold text-foreground mb-3">Operational KPIs</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {operationalKpis.map(kpi => (
            <Card pad={false} key={kpi.label} className="p-5">
              <div className="flex items-center gap-3">
                <div className={`p-2.5 rounded-lg ${kpi.color}`}>
                  <kpi.icon size={20} />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{kpi.label}</p>
                  <p className="text-2xl font-semibold text-foreground">{kpi.value}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card pad={false} className="p-4 lg:col-span-1">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-foreground">Notifications</h3>
            {unreadNotifications > 0 && <Badge variant="info">{unreadNotifications} unread</Badge>}
          </div>
          {notifications.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4 text-center">No recent activity</p>
          ) : (
            <div className="space-y-3">
              {notifications.slice(0, 8).map(n => (
                <div key={n.id} className="flex items-start gap-2">
                  <div className={`w-2 h-2 mt-1.5 rounded-full flex-shrink-0 ${n.is_read ? 'bg-muted-foreground/40' : 'bg-secondary'}`} />
                  <div className="min-w-0">
                    <p className="text-sm text-foreground truncate">{n.title}</p>
                    <p className="text-xs text-muted-foreground/70">{formatRelative(n.created_at)}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card pad={false} className="p-4 lg:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-foreground">Program Readiness</h3>
            <Button variant="ghost" size="sm" onClick={() => navigate('/i/programs')}>View All</Button>
          </div>
          {programs.length === 0 ? (
            <EmptyState
              icon={<BookOpen size={40} />}
              title="No programs yet"
              description="Create your first program to start accepting applications."
              action={{ label: 'Add Program', onClick: () => navigate('/i/programs/new') }}
            />
          ) : (
            <Table
              columns={programColumns}
              data={programs.slice(0, 5)}
              onRowClick={(row) => navigate(`/i/programs/${row.id}/edit`)}
            />
          )}
        </Card>
      </div>
    </div>
  )
}
