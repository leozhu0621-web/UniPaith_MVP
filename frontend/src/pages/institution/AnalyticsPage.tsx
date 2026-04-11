import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { BarChart3, TrendingUp, Target, Users, Award } from 'lucide-react'
import { getAnalytics, getDemandForecast } from '../../api/institutions'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Tabs from '../../components/ui/Tabs'
import Skeleton from '../../components/ui/Skeleton'
import InstitutionPageHeader from '../../components/institution/InstitutionPageHeader'
import { formatPercent } from '../../utils/format'
import type { AnalyticsData } from '../../types'

export default function AnalyticsPage() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('overview')
  const analyticsQ = useQuery({ queryKey: ['institution-analytics'], queryFn: getAnalytics })
  const demandQ = useQuery({ queryKey: ['demand-forecast'], queryFn: getDemandForecast, staleTime: 1000 * 60 * 15 })
  const analytics: AnalyticsData | undefined = analyticsQ.data

  const isLoading = analyticsQ.isLoading

  const kpis = [
    { label: 'Total Applications', value: analytics?.total_applications ?? 0, icon: Users, color: 'text-brand-slate-600 bg-brand-slate-100' },
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
          <button onClick={() => analyticsQ.refetch()} className="text-brand-slate-600 hover:underline text-sm">Retry</button>
        </Card>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <InstitutionPageHeader
        title="Insights"
        description="Track trends, diagnose bottlenecks, and monitor admissions outcomes over time."
        badge={<BarChart3 size={20} className="text-brand-slate-600" />}
        actions={(
          <Button variant="secondary" size="sm" onClick={() => navigate('/i/pipeline?tab=review')}>
            Open Needs Review
          </Button>
        )}
      />

      <Tabs
        tabs={[
          { id: 'overview', label: 'Overview' },
          { id: 'funnel', label: 'Funnel' },
          { id: 'attribution', label: 'Attribution' },
        ]}
        activeTab={activeTab}
        onChange={setActiveTab}
      />

      {activeTab === 'overview' && (<>
      {/* Executive KPI Cards */}
      <div>
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Executive Outcomes</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
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

      <h3 className="text-sm font-semibold text-gray-900">Operational Diagnostics</h3>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
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
                      className="bg-brand-slate-500 rounded-full h-2 transition-all"
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
                    className="w-full bg-brand-slate-500 rounded-t transition-all min-h-[4px]"
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

      {/* AI Demand Forecast */}
      {demandQ.data?.programs?.length ? (
        <Card className="p-5">
          <div className="flex items-center gap-2 mb-4">
            <Target size={18} className="text-brand-slate-600" />
            <h3 className="text-sm font-semibold text-gray-900">AI Demand Forecast</h3>
            <Badge variant="info">Next 30 days</Badge>
          </div>
          <div className="space-y-3">
            {demandQ.data.programs.map(p => {
              const signalColors: Record<string, string> = { high: 'bg-green-500', moderate: 'bg-amber-500', low: 'bg-gray-400' }
              return (
                <div key={p.program_id} className="flex items-center gap-4">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900 truncate">{p.program_name}</p>
                    <p className="text-xs text-gray-500">{p.degree_type} &middot; {p.active_matches} active matches</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${signalColors[p.demand_signal] ?? 'bg-gray-400'}`} />
                    <span className="text-xs text-gray-600 capitalize w-16">{p.demand_signal}</span>
                    <span className="text-sm font-medium text-gray-900 w-8 text-right">{p.recent_predictions}</span>
                  </div>
                </div>
              )
            })}
          </div>
        </Card>
      ) : null}
      </>)}

      {activeTab === 'funnel' && (
        <div className="space-y-4">
          <Card className="p-5">
            <h3 className="text-sm font-semibold text-gray-900 mb-4">Application Funnel</h3>
            {analytics?.funnel_stages?.length ? (() => {
              const maxCount = Math.max(...analytics.funnel_stages.map(s => s.count), 1)
              return (
                <div className="space-y-3">
                  {analytics.funnel_stages.map((stage) => (
                    <div key={stage.stage} className="flex items-center gap-4">
                      <div className="w-32 text-sm text-right text-gray-600 capitalize">{stage.stage.replace(/_/g, ' ')}</div>
                      <div className="flex-1">
                        <div
                          className="bg-brand-slate-500 rounded h-8 transition-all min-w-[4px]"
                          style={{ width: `${(stage.count / maxCount) * 100}%` }}
                        />
                      </div>
                      <div className="w-16 text-sm font-semibold text-gray-900">{stage.count}</div>
                      <div className="w-20 text-xs text-gray-500">
                        {stage.conversion_rate != null ? `${Math.round(stage.conversion_rate * 100)}% conv.` : ''}
                      </div>
                    </div>
                  ))}
                </div>
              )
            })() : (
              <p className="text-sm text-gray-500 text-center py-8">No funnel data yet. Applications will appear here once students apply.</p>
            )}
          </Card>
        </div>
      )}

      {activeTab === 'attribution' && (
        <div className="space-y-6">
          <Card className="p-5">
            <h3 className="text-sm font-semibold text-gray-900 mb-4">Campaign Performance</h3>
            {analytics?.campaign_attribution?.length ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-500 border-b">
                      <th className="py-2 pr-4">Campaign</th>
                      <th className="py-2 px-2 text-right">Recipients</th>
                      <th className="py-2 px-2 text-right">Delivered</th>
                      <th className="py-2 px-2 text-right">Opened</th>
                      <th className="py-2 px-2 text-right">Clicked</th>
                      <th className="py-2 pl-2 text-right">Apps Started</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analytics.campaign_attribution.map(c => (
                      <tr key={c.campaign_id} className="border-b border-gray-50">
                        <td className="py-2 pr-4 font-medium text-gray-900">{c.campaign_name}</td>
                        <td className="py-2 px-2 text-right">{c.recipients}</td>
                        <td className="py-2 px-2 text-right">{c.delivered}</td>
                        <td className="py-2 px-2 text-right">{c.opened}</td>
                        <td className="py-2 px-2 text-right">{c.clicked}</td>
                        <td className="py-2 pl-2 text-right">
                          <Badge variant={c.applications_started > 0 ? 'success' : 'neutral'}>{c.applications_started}</Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-sm text-gray-500 text-center py-8">No sent campaigns yet.</p>
            )}
          </Card>

          <Card className="p-5">
            <h3 className="text-sm font-semibold text-gray-900 mb-4">Event Performance</h3>
            {analytics?.event_attribution?.length ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-500 border-b">
                      <th className="py-2 pr-4">Event</th>
                      <th className="py-2 px-2 text-right">RSVPs</th>
                      <th className="py-2 px-2 text-right">Attended</th>
                      <th className="py-2 pl-2 text-right">Apps After</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analytics.event_attribution.map(e => (
                      <tr key={e.event_id} className="border-b border-gray-50">
                        <td className="py-2 pr-4 font-medium text-gray-900">{e.event_name}</td>
                        <td className="py-2 px-2 text-right">{e.rsvps}</td>
                        <td className="py-2 px-2 text-right">{e.attended}</td>
                        <td className="py-2 pl-2 text-right">
                          <Badge variant={e.applications_after > 0 ? 'success' : 'neutral'}>{e.applications_after}</Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-sm text-gray-500 text-center py-8">No events yet.</p>
            )}
          </Card>
        </div>
      )}
    </div>
  )
}
