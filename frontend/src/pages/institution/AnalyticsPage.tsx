import { useQuery } from '@tanstack/react-query'
import { BarChart3, TrendingUp, Target, Users, Award } from 'lucide-react'
import { getAnalytics } from '../../api/institutions'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Skeleton from '../../components/ui/Skeleton'
import { formatPercent } from '../../utils/format'
import type { AnalyticsData } from '../../types'

export default function AnalyticsPage() {
  const analyticsQ = useQuery({ queryKey: ['institution-analytics'], queryFn: getAnalytics })
  const analytics: AnalyticsData | undefined = analyticsQ.data

  const isLoading = analyticsQ.isLoading

  const kpis = [
    { label: 'Total Applications', value: analytics?.total_applications ?? 0, icon: Users, color: 'text-indigo-600 bg-indigo-100' },
    { label: 'Acceptance Rate', value: analytics?.acceptance_rate != null ? formatPercent(analytics.acceptance_rate) : '\u2014', icon: Target, color: 'text-green-600 bg-green-100' },
    { label: 'Avg Match Score', value: analytics?.avg_match_score != null ? `${Math.round(analytics.avg_match_score * 100)}` : '\u2014', icon: Award, color: 'text-amber-600 bg-amber-100' },
    { label: 'Yield Rate', value: analytics?.yield_rate != null ? formatPercent(analytics.yield_rate) : '\u2014', icon: TrendingUp, color: 'text-purple-600 bg-purple-100' },
  ]

  const statusCounts = analytics?.apps_by_status ?? {}
  const appsByProgram = analytics?.apps_by_program ?? []
  const appsByMonth = analytics?.apps_by_month ?? []
  const decisionsBreakdown = analytics?.decisions_breakdown ?? {}

  const maxStatusCount = Math.max(...Object.values(statusCounts), 1)
  const maxProgramCount = Math.max(...appsByProgram.map(p => p.count), 1)
  const maxMonthCount = Math.max(...appsByMonth.map(m => m.count), 1)
  const maxDecisionCount = Math.max(...Object.values(decisionsBreakdown), 1)

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-10 w-48" />
        <div className="grid grid-cols-4 gap-4">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-28" />)}</div>
        <Skeleton className="h-64" />
      </div>
    )
  }

  if (analyticsQ.isError) {
    return (
      <div className="p-6">
        <Card className="p-8 text-center">
          <p className="text-red-600 mb-2">Failed to load analytics</p>
          <button onClick={() => analyticsQ.refetch()} className="text-indigo-600 hover:underline text-sm">Retry</button>
        </Card>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-2">
        <BarChart3 size={24} className="text-indigo-600" />
        <h1 className="text-2xl font-bold text-gray-900">Insights</h1>
      </div>

      <Card className="p-4">
        <h3 className="text-sm font-semibold text-gray-900 mb-1">What this page is for</h3>
        <p className="text-sm text-gray-600">
          Use Insights for trend analysis and outcome reporting. For daily operations and queue work, use Overview and Applications.
        </p>
      </Card>

      {/* Executive KPI Cards */}
      <div>
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Executive Outcomes</h3>
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
      </div>

      <div className="grid grid-cols-2 gap-6">
        <Card className="p-4 border-dashed border-gray-300">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-900">Market & Demographics</h3>
            <Badge variant="neutral">Planned</Badge>
          </div>
          <p className="text-sm text-gray-600 mt-2">
            Next analytics phase will add applicant geography, demographic mix, channel attribution, and stage-duration insights.
          </p>
        </Card>
        <Card className="p-4 border-dashed border-gray-300">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-900">Operational Benchmarks</h3>
            <Badge variant="neutral">Planned</Badge>
          </div>
          <p className="text-sm text-gray-600 mt-2">
            Reviewer workload and conversion by cohort will be added once backend rollups are available.
          </p>
        </Card>
      </div>

      <h3 className="text-sm font-semibold text-gray-900">Operational Diagnostics</h3>

      <div className="grid grid-cols-2 gap-6">
        {/* Applications by Status */}
        <Card className="p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Applications by Status</h3>
          {Object.keys(statusCounts).length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-8">No data</p>
          ) : (
            <div className="space-y-3">
              {Object.entries(statusCounts).sort((a, b) => b[1] - a[1]).map(([status, count]) => (
                <div key={status}>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-gray-700 capitalize">{status.replace('_', ' ')}</span>
                    <span className="font-medium text-gray-900">{count}</span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2">
                    <div
                      className="bg-indigo-500 rounded-full h-2 transition-all"
                      style={{ width: `${(count / maxStatusCount) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Applications by Program */}
        <Card className="p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Applications by Program</h3>
          {appsByProgram.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-8">No data</p>
          ) : (
            <div className="space-y-3">
              {appsByProgram.map(({ program_name, count }) => (
                <div key={program_name}>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-gray-700 truncate max-w-[200px]">{program_name}</span>
                    <span className="font-medium text-gray-900">{count}</span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2">
                    <div
                      className="bg-emerald-500 rounded-full h-2 transition-all"
                      style={{ width: `${(count / maxProgramCount) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Applications Over Time */}
        <Card className="p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Applications Over Time</h3>
          {appsByMonth.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-8">No data</p>
          ) : (
            <div className="flex items-end gap-1 h-40">
              {appsByMonth.map(({ month, count }) => (
                <div key={month} className="flex-1 flex flex-col items-center gap-1">
                  <span className="text-xs font-medium text-gray-900">{count}</span>
                  <div
                    className="w-full bg-indigo-500 rounded-t transition-all min-h-[4px]"
                    style={{ height: `${(count / maxMonthCount) * 100}%` }}
                  />
                  <span className="text-[10px] text-gray-500 rotate-[-45deg] origin-top-left whitespace-nowrap">
                    {month.slice(5)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Decisions Breakdown */}
        <Card className="p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Decisions Breakdown</h3>
          {Object.keys(decisionsBreakdown).length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-8">No decisions yet</p>
          ) : (
            <div className="space-y-3">
              {Object.entries(decisionsBreakdown).sort((a, b) => b[1] - a[1]).map(([decision, count]) => {
                const colors: Record<string, string> = {
                  admitted: 'bg-green-500',
                  rejected: 'bg-red-500',
                  waitlisted: 'bg-amber-500',
                  deferred: 'bg-blue-500',
                }
                return (
                  <div key={decision}>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-gray-700 capitalize">{decision}</span>
                      <span className="font-medium text-gray-900">{count}</span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-2">
                      <div
                        className={`${colors[decision] ?? 'bg-gray-500'} rounded-full h-2 transition-all`}
                        style={{ width: `${(count / maxDecisionCount) * 100}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
