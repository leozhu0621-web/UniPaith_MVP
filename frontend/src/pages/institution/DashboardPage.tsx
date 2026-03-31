import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { LayoutDashboard, Plus, GitBranch, ClipboardCheck, Bell, BookOpen, MessageSquare, Calendar } from 'lucide-react'
import { getInstitution, getInstitutionPrograms } from '../../api/institutions'
import { getConversations } from '../../api/messaging'
import { getNotifications } from '../../api/notifications'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Skeleton from '../../components/ui/Skeleton'
import EmptyState from '../../components/ui/EmptyState'
import Table from '../../components/ui/Table'
import { formatDate, formatRelative, formatCurrency } from '../../utils/format'
import { DEGREE_LABELS } from '../../utils/constants'
import type { Notification, Conversation, Program } from '../../types'

export default function DashboardPage() {
  const navigate = useNavigate()

  const institutionQ = useQuery({ queryKey: ['institution'], queryFn: getInstitution, retry: false })
  const programsQ = useQuery({ queryKey: ['institution-programs'], queryFn: getInstitutionPrograms })
  const conversationsQ = useQuery({ queryKey: ['conversations'], queryFn: getConversations })
  const notificationsQ = useQuery({
    queryKey: ['notifications', { limit: 10 }],
    queryFn: () => getNotifications({ limit: 10 }),
  })

  const institution = institutionQ.data
  const programs: Program[] = Array.isArray(programsQ.data) ? programsQ.data : []
  const conversations: Conversation[] = Array.isArray(conversationsQ.data) ? conversationsQ.data : []
  const notifications: Notification[] = Array.isArray(notificationsQ.data) ? notificationsQ.data : []
  const unreadMessages = conversations.reduce((sum, c) => sum + (c.unread_count ?? 0), 0)

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

  if (!institution) {
    return (
      <div className="p-6">
        <Card className="p-8 text-center border-dashed border-2 border-indigo-300 bg-indigo-50/30">
          <LayoutDashboard size={48} className="mx-auto text-indigo-400 mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Welcome to UniPaith</h2>
          <p className="text-gray-600 mb-6 max-w-md mx-auto">
            Set up your institution profile and create your first program to start receiving applications.
          </p>
          <Button onClick={() => navigate('/i/setup')}>Get Started</Button>
        </Card>
      </div>
    )
  }

  const kpis = [
    { label: 'Programs', value: programs.length, icon: BookOpen, color: 'text-indigo-600 bg-indigo-100' },
    { label: 'Applications', value: '\u2014', icon: ClipboardCheck, color: 'text-emerald-600 bg-emerald-100' },
    { label: 'Unread Messages', value: unreadMessages, icon: MessageSquare, color: 'text-amber-600 bg-amber-100' },
    { label: 'Events', value: '\u2014', icon: Calendar, color: 'text-purple-600 bg-purple-100' },
  ]

  const programColumns = [
    { key: 'program_name', label: 'Name' },
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
      {/* Welcome */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Welcome back, {institution.name}</h1>
        <p className="text-sm text-gray-500 mt-1">Manage your programs, applications, and recruitment pipeline.</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4">
        {kpis.map(kpi => (
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

      {/* Quick Actions */}
      <Card className="p-4">
        <h3 className="text-sm font-medium text-gray-500 mb-3">Quick Actions</h3>
        <div className="flex gap-3">
          <Button onClick={() => navigate('/i/programs/new')} className="flex items-center gap-2">
            <Plus size={16} /> New Program
          </Button>
          <Button onClick={() => navigate('/i/pipeline')} variant="secondary" className="flex items-center gap-2">
            <GitBranch size={16} /> View Pipeline
          </Button>
          <Button onClick={() => navigate('/i/reviews')} variant="secondary" className="flex items-center gap-2">
            <ClipboardCheck size={16} /> Review Queue
          </Button>
        </div>
      </Card>

      {/* Two column layout */}
      <div className="grid grid-cols-3 gap-6">
        {/* Recent Activity */}
        <Card className="col-span-1 p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-gray-900">Recent Activity</h3>
            <Bell size={16} className="text-gray-400" />
          </div>
          {notifications.length === 0 ? (
            <p className="text-sm text-gray-500 py-4 text-center">No recent activity</p>
          ) : (
            <div className="space-y-3">
              {notifications.slice(0, 8).map(n => (
                <div key={n.id} className="flex items-start gap-2">
                  <div className={`w-2 h-2 mt-1.5 rounded-full flex-shrink-0 ${n.is_read ? 'bg-gray-300' : 'bg-indigo-500'}`} />
                  <div className="min-w-0">
                    <p className="text-sm text-gray-800 truncate">{n.title}</p>
                    <p className="text-xs text-gray-400">{formatRelative(n.created_at)}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Programs Overview */}
        <Card className="col-span-2 p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-gray-900">Programs Overview</h3>
            <Button variant="ghost" size="sm" onClick={() => navigate('/i/programs')}>View All</Button>
          </div>
          {programs.length === 0 ? (
            <EmptyState
              icon={<BookOpen size={40} />}
              title="No programs yet"
              description="Create your first program to start accepting applications."
              action={{ label: 'New Program', onClick: () => navigate('/i/programs/new') }}
            />
          ) : (
            <Table
              columns={programColumns}
              data={programs.slice(0, 5)}
              onRowClick={(row) => navigate(`/i/programs/${row.id}`)}
            />
          )}
        </Card>
      </div>
    </div>
  )
}
