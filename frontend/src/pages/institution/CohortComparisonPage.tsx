import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Users, BarChart3, ChevronDown, ChevronUp } from 'lucide-react'
import { getApplicationsByProgram } from '../../api/applications-admin'
import { getCohortComparison } from '../../api/reviews'
import { getInstitutionPrograms } from '../../api/institutions'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Select from '../../components/ui/Select'
import Skeleton from '../../components/ui/Skeleton'
import EmptyState from '../../components/ui/EmptyState'
import InstitutionPageHeader from '../../components/institution/InstitutionPageHeader'
import { formatScore } from '../../utils/format'
import type { Application, CohortApplicant, Program } from '../../types'

const DECISION_COLORS: Record<string, string> = {
  admitted: 'text-green-600 bg-green-50',
  rejected: 'text-red-600 bg-red-50',
  waitlisted: 'text-amber-600 bg-amber-50',
  deferred: 'text-blue-600 bg-blue-50',
}

export default function CohortComparisonPage() {
  const [selectedProgram, setSelectedProgram] = useState('')
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [sortBy, setSortBy] = useState<'avg_score' | 'match_score' | 'student_name'>('avg_score')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [expandedCriteria, setExpandedCriteria] = useState<string | null>(null)

  const programsQ = useQuery({ queryKey: ['institution-programs'], queryFn: getInstitutionPrograms })
  const programs: Program[] = Array.isArray(programsQ.data) ? programsQ.data : []
  const programOptions = [{ value: '', label: 'Select Program...' }, ...programs.map(p => ({ value: p.id, label: p.program_name }))]

  const appsQ = useQuery({
    queryKey: ['compare-apps', selectedProgram],
    queryFn: () => getApplicationsByProgram(selectedProgram),
    enabled: !!selectedProgram,
  })
  const allApps: Application[] = Array.isArray(appsQ.data) ? appsQ.data : []

  const cohortQ = useQuery({
    queryKey: ['cohort-compare', selectedIds],
    queryFn: () => getCohortComparison(selectedIds),
    enabled: selectedIds.length >= 2,
  })
  const applicants: CohortApplicant[] = cohortQ.data?.applicants ?? []

  const sorted = useMemo(() => {
    const arr = [...applicants]
    arr.sort((a, b) => {
      let va: number | string = 0
      let vb: number | string = 0
      if (sortBy === 'avg_score') { va = a.avg_score ?? -1; vb = b.avg_score ?? -1 }
      else if (sortBy === 'match_score') { va = a.match_score ?? -1; vb = b.match_score ?? -1 }
      else { va = a.student_name; vb = b.student_name }
      if (va < vb) return sortDir === 'asc' ? -1 : 1
      if (va > vb) return sortDir === 'asc' ? 1 : -1
      return 0
    })
    return arr
  }, [applicants, sortBy, sortDir])

  // Collect all unique criterion names across all scores
  const allCriteria = useMemo(() => {
    const names = new Set<string>()
    for (const a of applicants) {
      for (const s of a.scores) {
        if (s.criterion_scores) Object.keys(s.criterion_scores).forEach(k => names.add(k))
      }
    }
    return Array.from(names).sort()
  }, [applicants])

  const toggleApp = (id: string) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])
  }

  const toggleSort = (col: typeof sortBy) => {
    if (sortBy === col) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortBy(col); setSortDir('desc') }
  }

  const SortIcon = ({ col }: { col: typeof sortBy }) => {
    if (sortBy !== col) return null
    return sortDir === 'desc' ? <ChevronDown size={12} /> : <ChevronUp size={12} />
  }

  return (
    <div className="p-6 space-y-4">
      <InstitutionPageHeader
        title="Cohort Comparison"
        description="Side-by-side comparison of applicants on rubric scores and key fields for calibration."
      />

      {/* Program selector */}
      <Card className="p-4">
        <div className="flex items-center gap-4">
          <Select label="Program" options={programOptions} value={selectedProgram} onChange={e => { setSelectedProgram(e.target.value); setSelectedIds([]) }} />
          {selectedIds.length > 0 && (
            <Badge variant="info">{selectedIds.length} selected for comparison</Badge>
          )}
        </div>
      </Card>

      {/* Application picker */}
      {selectedProgram && (
        <Card className="p-4">
          <p className="text-sm font-medium text-gray-700 mb-2">Select 2+ applicants to compare:</p>
          {appsQ.isLoading ? (
            <Skeleton className="h-20" />
          ) : allApps.length === 0 ? (
            <p className="text-sm text-gray-500">No applications for this program.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {allApps.map(app => (
                <button
                  key={app.id}
                  onClick={() => toggleApp(app.id)}
                  className={`px-3 py-1.5 rounded-lg border text-sm transition-all ${
                    selectedIds.includes(app.id)
                      ? 'bg-brand-slate-50 border-brand-slate-400 text-brand-slate-700 font-medium'
                      : 'bg-white border-gray-200 text-gray-600 hover:border-gray-400'
                  }`}
                >
                  {app.student_id.slice(0, 8)} {app.match_score != null && `(${formatScore(app.match_score / 100)})`}
                </button>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Comparison Table */}
      {selectedIds.length < 2 ? (
        <EmptyState icon={<Users size={40} />} title="Select applicants" description="Pick 2 or more applicants from the same program to see their side-by-side comparison." />
      ) : cohortQ.isLoading ? (
        <Skeleton className="h-80" />
      ) : sorted.length === 0 ? (
        <EmptyState icon={<BarChart3 size={40} />} title="No data" description="No comparison data available for the selected applicants." />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b bg-gray-50">
                <th className="text-left px-3 py-2 font-medium text-gray-600 sticky left-0 bg-gray-50 z-10">Field</th>
                {sorted.map(a => (
                  <th key={a.application_id} className="text-center px-4 py-2 font-medium text-gray-900 min-w-[140px]">
                    {a.student_name || a.student_id.slice(0, 8)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {/* Status */}
              <tr className="border-b">
                <td className="px-3 py-2 font-medium text-gray-500 sticky left-0 bg-white">Status</td>
                {sorted.map(a => (
                  <td key={a.application_id} className="text-center px-4 py-2">
                    <Badge variant="info">{a.status ?? '—'}</Badge>
                  </td>
                ))}
              </tr>
              {/* Decision */}
              <tr className="border-b">
                <td className="px-3 py-2 font-medium text-gray-500 sticky left-0 bg-white">Decision</td>
                {sorted.map(a => (
                  <td key={a.application_id} className="text-center px-4 py-2">
                    {a.decision ? (
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${DECISION_COLORS[a.decision] ?? ''}`}>{a.decision}</span>
                    ) : '—'}
                  </td>
                ))}
              </tr>
              {/* Match Score */}
              <tr className="border-b hover:bg-gray-50 cursor-pointer" onClick={() => toggleSort('match_score')}>
                <td className="px-3 py-2 font-medium text-gray-500 sticky left-0 bg-white flex items-center gap-1">
                  Match Score <SortIcon col="match_score" />
                </td>
                {sorted.map(a => (
                  <td key={a.application_id} className="text-center px-4 py-2 font-mono">
                    {a.match_score != null ? formatScore(a.match_score / 100) : '—'}
                  </td>
                ))}
              </tr>
              {/* Avg Rubric Score */}
              <tr className="border-b bg-blue-50/50 hover:bg-blue-50 cursor-pointer" onClick={() => toggleSort('avg_score')}>
                <td className="px-3 py-2 font-semibold text-gray-700 sticky left-0 bg-blue-50/50 flex items-center gap-1">
                  Avg Rubric Score <SortIcon col="avg_score" />
                </td>
                {sorted.map(a => (
                  <td key={a.application_id} className="text-center px-4 py-2 font-bold text-gray-900">
                    {a.avg_score != null ? a.avg_score.toFixed(1) : '—'}
                  </td>
                ))}
              </tr>
              {/* Per-criterion scores */}
              {allCriteria.length > 0 && (
                <>
                  <tr className="border-b cursor-pointer hover:bg-gray-50" onClick={() => setExpandedCriteria(expandedCriteria ? null : 'all')}>
                    <td colSpan={sorted.length + 1} className="px-3 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider">
                      {expandedCriteria ? '▼' : '▶'} Rubric Criteria ({allCriteria.length})
                    </td>
                  </tr>
                  {expandedCriteria && allCriteria.map(criterion => (
                    <tr key={criterion} className="border-b">
                      <td className="px-3 py-1.5 text-gray-500 text-xs pl-6 sticky left-0 bg-white">{criterion}</td>
                      {sorted.map(a => {
                        const latest = a.scores[0]
                        const val = latest?.criterion_scores?.[criterion]
                        return (
                          <td key={a.application_id} className="text-center px-4 py-1.5 text-xs font-mono">
                            {val != null ? val : '—'}
                          </td>
                        )
                      })}
                    </tr>
                  ))}
                </>
              )}
              {/* Completeness */}
              <tr className="border-b">
                <td className="px-3 py-2 font-medium text-gray-500 sticky left-0 bg-white">Completeness</td>
                {sorted.map(a => (
                  <td key={a.application_id} className="text-center px-4 py-2">
                    <Badge variant={a.completeness_status === 'complete' ? 'success' : a.completeness_status === 'incomplete' ? 'warning' : 'neutral'}>
                      {a.completeness_status ?? '—'}
                    </Badge>
                  </td>
                ))}
              </tr>
              {/* GPA */}
              <tr className="border-b">
                <td className="px-3 py-2 font-medium text-gray-500 sticky left-0 bg-white">GPA</td>
                {sorted.map(a => (
                  <td key={a.application_id} className="text-center px-4 py-2 font-mono">
                    {a.gpa != null ? a.gpa.toFixed(2) : '—'}
                  </td>
                ))}
              </tr>
              {/* Nationality */}
              <tr className="border-b">
                <td className="px-3 py-2 font-medium text-gray-500 sticky left-0 bg-white">Nationality</td>
                {sorted.map(a => (
                  <td key={a.application_id} className="text-center px-4 py-2">
                    {a.nationality ?? '—'}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
