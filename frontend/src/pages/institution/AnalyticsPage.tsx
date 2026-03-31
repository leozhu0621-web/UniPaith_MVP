import { useMemo } from 'react'
import { useQuery, useQueries } from '@tanstack/react-query'
import { BarChart3, TrendingUp, Target, Users, Award } from 'lucide-react'
import { getInstitutionPrograms } from '../../api/institutions'
import { getApplicationsByProgram } from '../../api/applications-admin'
import Card from '../../components/ui/Card'
import Skeleton from '../../components/ui/Skeleton'
import { formatPercent } from '../../utils/format'
import type { Program, Application } from '../../types'

export default function AnalyticsPage() {
  const programsQ = useQuery({ queryKey: ['institution-programs'], queryFn: getInstitutionPrograms })
  const programs: Program[] = useMemo(
    () => (Array.isArray(programsQ.data) ? programsQ.data : []),
    [programsQ.data],
  )

  const appQueries = useQueries({
    queries: programs.map(p => ({
      queryKey: ['analytics-apps', p.id],
      queryFn: () => getApplicationsByProgram(p.id),
      enabled: programs.length > 0,
    })),
  })

  const allApps: Application[] = appQueries.flatMap(q => (Array.isArray(q.data) ? q.data : []))

  const isLoading = programsQ.isLoading || appQueries.some(q => q.isLoading)

  // Computed KPIs
  const totalApps = allApps.length
  const admittedCount = allApps.filter(a => a.decision === 'admitted').length
  const decidedCount = allApps.filter(a => a.decision != null).length
  const acceptanceRate = decidedCount > 0 ? admittedCount / decidedCount : null
  const avgScore = allApps.filter(a => a.match_score != null).length > 0
    ? allApps.filter(a => a.match_score != null).reduce((s, a) => s + (a.match_score ?? 0), 0) / allApps.filter(a => a.match_score != null).length
    : null
  // yieldRate: Needs enrollment data (Phase 2)

  // Status distribution
  const statusCounts = useMemo(() => {
    const counts: Record<string, number> = {}
    allApps.forEach(a => { counts[a.status] = (counts[a.status] ?? 0) + 1 })
    return counts
  }, [allApps])

  // By program
  const appsByProgram = useMemo(() => {
    const map: Record<string, number> = {}
    allApps.forEach(a => {
      const progName = programs.find(p => p.id === a.program_id)?.program_name ?? a.program_id.slice(0, 8)
      map[progName] = (map[progName] ?? 0) + 1
    })
    return map
  }, [allApps, programs])

  const kpis = [
    { label: 'Total Applications', value: totalApps, icon: Users, color: 'text-indigo-600 bg-indigo-100' },
    { label: 'Acceptance Rate', value: acceptanceRate != null ? formatPercent(acceptanceRate) : '\u2014', icon: Target, color: 'text-green-600 bg-green-100' },
    { label: 'Avg Match Score', value: avgScore != null ? `${Math.round(avgScore)}` : '\u2014', icon: Award, color: 'text-amber-600 bg-amber-100' },
    { label: 'Yield Rate', value: '\u2014', icon: TrendingUp, color: 'text-purple-600 bg-purple-100' },
  ]

  const maxStatusCount = Math.max(...Object.values(statusCounts), 1)
  const maxProgramCount = Math.max(...Object.values(appsByProgram), 1)

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-10 w-48" />
        <div className="grid grid-cols-4 gap-4">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-28" />)}</div>
        <Skeleton className="h-64" />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-2">
        <BarChart3 size={24} className="text-indigo-600" />
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
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
          {Object.keys(appsByProgram).length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-8">No data</p>
          ) : (
            <div className="space-y-3">
              {Object.entries(appsByProgram).sort((a, b) => b[1] - a[1]).map(([prog, count]) => (
                <div key={prog}>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-gray-700 truncate max-w-[200px]">{prog}</span>
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
      </div>
    </div>
  )
}
