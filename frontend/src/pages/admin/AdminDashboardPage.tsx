import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  getSystemStats, getPlatformStats,
} from '../../api/admin'
import { formatRelative } from '../../utils/format'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Skeleton from '../../components/ui/Skeleton'
import Button from '../../components/ui/Button'
import {
  Users, GraduationCap, FileText, Building2, Activity,
  Target, RefreshCw, Cpu, Mail, Database,
} from 'lucide-react'

function KPICard({ icon: Icon, label, value, sub, color }: {
  icon: any; label: string; value: string | number; sub?: string; color: string
}) {
  return (
    <Card className="p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-gray-500">{label}</p>
          <p className="text-3xl font-bold mt-1 text-gray-900">{value}</p>
          {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
        </div>
        <div className={`p-2.5 rounded-lg ${color}`}>
          <Icon size={20} />
        </div>
      </div>
    </Card>
  )
}

function BarSegment({ label, value, total, color }: {
  label: string; value: number; total: number; color: string
}) {
  const pct = total > 0 ? (value / total) * 100 : 0
  return (
    <div className="flex items-center gap-3 mb-2">
      <span className="w-28 text-sm text-right text-gray-600">{label}</span>
      <div className="flex-1 bg-gray-100 rounded-full h-5">
        <div className={`${color} rounded-full h-5 transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-8 text-sm text-right font-medium">{value}</span>
    </div>
  )
}

const STAGE_DOT: Record<string, string> = {
  running: 'bg-green-500',
  local_online: 'bg-green-500',
  waiting: 'bg-yellow-400',
  completed: 'bg-green-500',
  error: 'bg-red-500',
  paused: 'bg-gray-400',
  off: 'bg-gray-300',
  not_started: 'bg-gray-300',
}

export default function AdminDashboardPage() {
  const navigate = useNavigate()
  const { data: stats, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['admin', 'stats'],
    queryFn: getSystemStats,
    refetchInterval: 30000,
  })

  const { data: platformStats } = useQuery({
    queryKey: ['admin', 'platform-stats'],
    queryFn: getPlatformStats,
  })

  if (isLoading) {
    return (
      <div className="p-8 space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-28" />)}
        </div>
      </div>
    )
  }

  const appTotal = stats?.applications?.total ?? 0
  const byStatus = stats?.applications?.by_status ?? {}
  const byDecision = stats?.applications?.by_decision ?? {}
  const pipeline = stats?.pipeline ?? {}
  const frontier = pipeline?.frontier ?? {}
  const stages = pipeline?.stages ?? {}
  const recs = stats?.recommendations ?? {}
  const recByStatus = recs?.by_status ?? {}

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">System Overview</h1>
          <p className="text-sm text-gray-500">Real-time platform metrics and activity</p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex items-center gap-2 px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
        >
          <RefreshCw size={14} className={isFetching ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      <Card className="p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-indigo-100 text-indigo-600"><Cpu size={18} /></div>
          <div>
            <p className="text-sm font-medium text-gray-800">AI Engine</p>
            <p className="text-xs text-gray-500">Monitor, control, and maintain the AI pipeline from one place.</p>
          </div>
        </div>
        <Button size="sm" onClick={() => navigate('/admin/ai')}>Open AI Center</Button>
      </Card>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          icon={Users}
          label="Total Users"
          value={stats?.users?.total ?? platformStats?.total_users ?? 0}
          sub={`${stats?.users?.students ?? 0} students, ${stats?.users?.institutions ?? 0} inst.`}
          color="bg-blue-100 text-blue-600"
        />
        <KPICard
          icon={Building2}
          label="Institutions"
          value={stats?.institutions ?? platformStats?.total_institutions ?? 0}
          color="bg-purple-100 text-purple-600"
        />
        <KPICard
          icon={GraduationCap}
          label="Programs"
          value={stats?.programs?.total ?? platformStats?.total_programs ?? 0}
          sub={`${stats?.programs?.published ?? 0} published`}
          color="bg-green-100 text-green-600"
        />
        <KPICard
          icon={FileText}
          label="Applications"
          value={appTotal || platformStats?.total_applications || 0}
          color="bg-orange-100 text-orange-600"
        />
        <KPICard
          icon={Users}
          label="Student Profiles"
          value={stats?.profiles ?? 0}
          color="bg-indigo-100 text-indigo-600"
        />
        <KPICard
          icon={Target}
          label="Match Results"
          value={stats?.matching?.total_matches ?? 0}
          sub={`Avg score: ${stats?.matching?.avg_score ?? 0}%`}
          color="bg-cyan-100 text-cyan-600"
        />
        <KPICard
          icon={Mail}
          label="Recommendations"
          value={recs?.total ?? 0}
          sub={`${recByStatus.submitted ?? 0} submitted, ${recByStatus.requested ?? 0} pending`}
          color="bg-rose-100 text-rose-600"
        />
        <KPICard
          icon={Activity}
          label="Engagement Signals"
          value={stats?.engagement?.total_signals ?? 0}
          color="bg-amber-100 text-amber-600"
        />
      </div>

      {/* Pipeline status row */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-700">Pipeline Status</h3>
          <Button size="sm" variant="secondary" onClick={() => navigate('/admin/ai')}>
            Manage
          </Button>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          {(['crawl', 'extract', 'ml'] as const).map(stage => {
            const s = stages[stage] ?? { status: 'not_started' }
            const dotColor = STAGE_DOT[s.status] || 'bg-gray-300'
            return (
              <div key={stage} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className={`h-2.5 w-2.5 rounded-full ${dotColor}`} />
                  <span className="text-sm font-semibold text-gray-800 capitalize">{stage}</span>
                  <span className="text-xs text-gray-400 ml-auto">{s.status}</span>
                </div>
                <div className="text-xs text-gray-500 space-y-1">
                  <div className="flex justify-between">
                    <span>Processed</span>
                    <span className="font-mono text-gray-800">{s.items_processed_total ?? 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>This hour</span>
                    <span className="font-mono text-gray-800">{s.items_processed_hour ?? 0}</span>
                  </div>
                </div>
              </div>
            )
          })}
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Database size={14} className="text-gray-500" />
              <span className="text-sm font-semibold text-gray-800">Frontier</span>
            </div>
            <div className="text-xs text-gray-500 space-y-1">
              <div className="flex justify-between">
                <span>Pending</span>
                <span className="font-mono text-yellow-600">{frontier.pending ?? 0}</span>
              </div>
              <div className="flex justify-between">
                <span>Completed</span>
                <span className="font-mono text-green-600">{frontier.completed ?? 0}</span>
              </div>
              <div className="flex justify-between">
                <span>Failed</span>
                <span className="font-mono text-red-600">{frontier.failed ?? 0}</span>
              </div>
              <div className="flex justify-between border-t border-gray-100 pt-1 mt-1">
                <span>Knowledge docs</span>
                <span className="font-mono text-gray-800">{pipeline.knowledge_docs ?? 0}</span>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Applications by Status</h3>
          {appTotal === 0 ? (
            <p className="text-sm text-gray-400 text-center py-8">No applications yet</p>
          ) : (
            <>
              <BarSegment label="Draft" value={byStatus.draft ?? 0} total={appTotal} color="bg-gray-400" />
              <BarSegment label="Submitted" value={byStatus.submitted ?? 0} total={appTotal} color="bg-blue-500" />
              <BarSegment label="Under Review" value={byStatus.under_review ?? 0} total={appTotal} color="bg-yellow-500" />
              <BarSegment label="Interview" value={byStatus.interview ?? 0} total={appTotal} color="bg-purple-500" />
              <BarSegment label="Decision" value={byStatus.decision_made ?? 0} total={appTotal} color="bg-orange-500" />
            </>
          )}
        </Card>

        <Card className="p-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Decision Breakdown</h3>
          {(byDecision.admitted ?? 0) + (byDecision.rejected ?? 0) === 0 ? (
            <p className="text-sm text-gray-400 text-center py-8">No decisions yet</p>
          ) : (
            <>
              <BarSegment label="Admitted" value={byDecision.admitted ?? 0} total={appTotal} color="bg-green-500" />
              <BarSegment label="Rejected" value={byDecision.rejected ?? 0} total={appTotal} color="bg-red-500" />
              <BarSegment label="Waitlisted" value={byDecision.waitlisted ?? 0} total={appTotal} color="bg-yellow-500" />
              <BarSegment label="Deferred" value={byDecision.deferred ?? 0} total={appTotal} color="bg-gray-400" />
            </>
          )}
        </Card>
      </div>

      {/* Recent activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Recent Users</h3>
          {(stats?.recent_users?.length ?? 0) === 0 ? (
            <p className="text-sm text-gray-400 text-center py-8">No users yet</p>
          ) : (
            <div className="space-y-2">
              {stats.recent_users.map((u: any) => (
                <div key={u.id} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                  <div>
                    <p className="text-sm font-medium text-gray-800">{u.email}</p>
                    <p className="text-xs text-gray-500">{formatRelative(u.created_at)}</p>
                  </div>
                  <Badge variant={u.role === 'student' ? 'info' : u.role === 'institution_admin' ? 'success' : 'neutral'}>
                    {u.role}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card className="p-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Recent Applications</h3>
          {(stats?.recent_applications?.length ?? 0) === 0 ? (
            <p className="text-sm text-gray-400 text-center py-8">No applications yet</p>
          ) : (
            <div className="space-y-2">
              {stats.recent_applications.map((a: any) => (
                <div key={a.id} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                  <div>
                    <p className="text-sm font-medium text-gray-800">Student: {a.student_id.slice(0, 8)}...</p>
                    <p className="text-xs text-gray-500">{formatRelative(a.created_at)}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={
                      a.status === 'submitted' ? 'info' :
                      a.status === 'under_review' ? 'warning' :
                      a.status === 'decision_made' ? 'success' : 'neutral'
                    }>
                      {a.status}
                    </Badge>
                    {a.decision && (
                      <Badge variant={a.decision === 'admitted' ? 'success' : 'danger'}>
                        {a.decision}
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
