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
} from 'lucide-react'
import { getInstitution, getInstitutionPrograms, getDashboardSummary } from '../../api/institutions'
import { getNotifications } from '../../api/notifications'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Skeleton from '../../components/ui/Skeleton'
import EmptyState from '../../components/ui/EmptyState'
import Table from '../../components/ui/Table'
import { formatDate, formatRelative, formatCurrency, formatPercent } from '../../utils/format'
import { DEGREE_LABELS } from '../../utils/constants'
import type { Notification, Program, DashboardSummary } from '../../types'

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

  const institution = institutionQ.data
  const programs: Program[] = Array.isArray(programsQ.data) ? programsQ.data : []
  const summary: DashboardSummary | undefined = summaryQ.data
  const notifications: Notification[] = Array.isArray(notificationsQ.data) ? notificationsQ.data : []

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
        <Card className="p-8 text-center border-dashed border-2 border-brand-slate-300 bg-brand-slate-50/30">
          <LayoutDashboard size={48} className="mx-auto text-brand-slate-400 mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Welcome to UniPaith</h2>
          <p className="text-gray-600 mb-6 max-w-md mx-auto">
            Set up your institution profile and create your first program to start receiving applications.
          </p>
          <Button onClick={() => navigate('/i/setup')}>Get Started</Button>
        </Card>
      </div>
    )
  }

  if (!institution) return null

  const executiveKpis = [
    {
      label: 'Applications',
      value: summary?.total_applications ?? 0,
      icon: Users,
      color: 'text-brand-slate-600 bg-brand-slate-100',
    },
    {
      label: 'Acceptance Rate',
      value: summary?.acceptance_rate != null ? formatPercent(summary.acceptance_rate) : '-',
      icon: Target,
      color: 'text-emerald-600 bg-emerald-100',
    },
    {
      label: 'Yield Rate',
      value: summary?.yield_rate != null ? formatPercent(summary.yield_rate) : '-',
      icon: TrendingUp,
      color: 'text-purple-600 bg-purple-100',
    },
    {
      label: 'Needs Review',
      value: summary?.pending_review_count ?? 0,
      icon: ClipboardCheck,
      color: 'text-amber-600 bg-amber-100',
    },
  ]

  const operationalKpis = [
    {
      label: 'Programs Published',
      value: `${summary?.published_program_count ?? 0}/${summary?.program_count ?? programs.length}`,
      icon: BookOpen,
      color: 'text-blue-600 bg-blue-100',
    },
    {
      label: 'Active Events',
      value: summary?.active_events_count ?? 0,
      icon: Calendar,
      color: 'text-pink-600 bg-pink-100',
    },
    {
      label: 'Unread Inbox',
      value: summary?.unread_messages_count ?? 0,
      icon: Mail,
      color: 'text-slate-600 bg-slate-100',
    },
  ]
  const priorityItems = [
    {
      label: 'Applications waiting for review',
      value: summary?.pending_review_count ?? 0,
      actionLabel: 'Open Queue',
      onClick: () => navigate('/i/pipeline?tab=review'),
    },
    {
      label: 'Unread applicant conversations',
      value: summary?.unread_messages_count ?? 0,
      actionLabel: 'Open Inbox',
      onClick: () => navigate('/i/messages'),
    },
    {
      label: 'Programs still in draft',
      value: (summary?.program_count ?? programs.length) - (summary?.published_program_count ?? 0),
      actionLabel: 'Publish Programs',
      onClick: () => navigate('/i/programs'),
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
        <h1 className="text-2xl font-bold text-gray-900">Welcome back, {institution.name}</h1>
        <p className="text-sm text-gray-500 mt-1">
          Run today&apos;s admissions workload, track outcomes, and take next actions from one place.
        </p>
      </div>

      <Card className="p-4">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Today&apos;s Action Panel</h3>
        <div className="flex flex-wrap gap-2">
          <Button onClick={() => navigate('/i/programs/new')} className="flex items-center gap-2">
            <Plus size={16} /> Add Program
          </Button>
          <Button onClick={() => navigate('/i/pipeline?tab=review')} variant="secondary" className="flex items-center gap-2">
            <ClipboardCheck size={16} /> Triage Review Queue
          </Button>
          <Button onClick={() => navigate('/i/pipeline?tab=board')} variant="secondary" className="flex items-center gap-2">
            <GitBranch size={16} /> Open Applications Board
          </Button>
          <Button onClick={() => navigate('/i/campaigns')} variant="secondary" className="flex items-center gap-2">
            <Bell size={16} /> Launch Outreach
          </Button>
        </div>
      </Card>

      <Card className="p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-900">Today&apos;s Priorities</h3>
          <Badge variant="info">Operations</Badge>
        </div>
        <div className="space-y-2">
          {priorityItems.map(item => (
            <div key={item.label} className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 rounded-lg border border-gray-200 px-3 py-2">
              <div>
                <p className="text-sm text-gray-700">{item.label}</p>
                <p className="text-xs text-gray-500">Current count: {item.value}</p>
              </div>
              <Button size="sm" variant="secondary" onClick={item.onClick} className="self-start sm:self-auto">
                {item.actionLabel}
              </Button>
            </div>
          ))}
        </div>
      </Card>

      <div>
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Executive KPIs</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
          {executiveKpis.map(kpi => (
            <Card key={kpi.label} className="p-5">
              <div className="flex items-center gap-3">
                <div className={`p-2.5 rounded-lg ${kpi.color}`}>
                  <kpi.icon size={20} />
                </div>
                <div>
                  <p className="text-sm text-gray-500">{kpi.label}</p>
                  <p className="text-2xl font-semibold text-gray-900">{kpi.value}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Operational KPIs</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {operationalKpis.map(kpi => (
            <Card key={kpi.label} className="p-5">
              <div className="flex items-center gap-3">
                <div className={`p-2.5 rounded-lg ${kpi.color}`}>
                  <kpi.icon size={20} />
                </div>
                <div>
                  <p className="text-sm text-gray-500">{kpi.label}</p>
                  <p className="text-2xl font-semibold text-gray-900">{kpi.value}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-900">Activity Feed</h3>
            <Bell size={16} className="text-gray-400" />
          </div>
          {notifications.length === 0 ? (
            <p className="text-sm text-gray-500 py-4 text-center">No recent activity</p>
          ) : (
            <div className="space-y-3">
              {notifications.slice(0, 8).map(n => (
                <div key={n.id} className="flex items-start gap-2">
                  <div className={`w-2 h-2 mt-1.5 rounded-full flex-shrink-0 ${n.is_read ? 'bg-gray-300' : 'bg-brand-slate-500'}`} />
                  <div className="min-w-0">
                    <p className="text-sm text-gray-800 truncate">{n.title}</p>
                    <p className="text-xs text-gray-400">{formatRelative(n.created_at)}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card className="p-4 lg:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-900">Program Readiness</h3>
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
