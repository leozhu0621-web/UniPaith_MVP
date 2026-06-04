import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Users, BarChart3, ChevronDown, ChevronUp, Scale, AlertTriangle } from 'lucide-react'
import { getApplicationsByProgram } from '../../api/applications-admin'
import { getCohortComparison, getReviewCalibration } from '../../api/reviews'
import { getInstitutionPrograms } from '../../api/institutions'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Select from '../../components/ui/Select'
import Skeleton from '../../components/ui/Skeleton'
import EmptyState from '../../components/ui/EmptyState'
import Button from '../../components/ui/Button'
import QueryError from '../../components/ui/QueryError'
import InstitutionPageHeader from '../../components/institution/InstitutionPageHeader'
import { formatScore } from '../../utils/format'
import type { Application, CohortApplicant, Program } from '../../types'

// Brand-tokened decision chips (§5 decision-colored chips).
const DECISION_COLORS: Record<string, string> = {
  admitted: 'text-success bg-success-soft',
  rejected: 'text-error bg-error-soft',
  waitlisted: 'text-warning bg-warning-soft',
  deferred: 'text-secondary bg-secondary/10',
}

const applicantLabel = (a: { student_name?: string | null; student_id: string }) =>
  a.student_name ?? `Applicant ${a.student_id.slice(0, 8)}`

export default function CohortComparisonPage({ embedded = false }: { embedded?: boolean }) {
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
  const applicants: CohortApplicant[] = useMemo(() => cohortQ.data?.applicants ?? [], [cohortQ.data])

  // Reader calibration (§7A.2) — program-scoped inter-rater reliability + drift.
  const calibrationQ = useQuery({
    queryKey: ['review-calibration', selectedProgram],
    queryFn: () => getReviewCalibration(selectedProgram || undefined),
    enabled: !!selectedProgram,
  })
  const calibration = calibrationQ.data

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

  const selectAll = () => setSelectedIds(allApps.map(a => a.id))
  const clearSelection = () => setSelectedIds([])

  const toggleSort = (col: typeof sortBy) => {
    if (sortBy === col) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortBy(col); setSortDir('desc') }
  }

  const SortIcon = ({ col }: { col: typeof sortBy }) => {
    if (sortBy !== col) return null
    return sortDir === 'desc' ? <ChevronDown size={12} /> : <ChevronUp size={12} />
  }

  const inner = (
    <div className="space-y-4">
      {!embedded && (
        <InstitutionPageHeader
          title="Cohort Comparison"
          description="Side-by-side comparison of applicants on rubric scores and key fields for calibration."
        />
      )}

      {/* Program selector */}
      <Card className="p-4">
        <div className="flex items-center gap-4">
          <Select label="Program" options={programOptions} value={selectedProgram} onChange={e => { setSelectedProgram(e.target.value); setSelectedIds([]) }} />
          {selectedIds.length > 0 && (
            <Badge variant="info">{selectedIds.length} selected for comparison</Badge>
          )}
        </div>
      </Card>

      {/* Reader calibration (§7A.2) — coaching signals only */}
      {selectedProgram && calibration && (calibration.reviewer_drift.length > 0 || calibration.inter_rater.length > 0) && (
        <Card className="p-4 space-y-3">
          <div className="flex items-center gap-2">
            <Scale size={16} className="text-secondary" />
            <h3 className="text-sm font-semibold text-foreground">Reader calibration</h3>
            <Badge variant="neutral">coaching only</Badge>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1.5">Inter-rater reliability</p>
              {calibration.inter_rater.length === 0 ? (
                <p className="text-xs text-muted-foreground">Not enough multi-reviewer scores yet.</p>
              ) : (
                <div className="space-y-1">
                  {calibration.inter_rater.slice(0, 6).map(c => (
                    <div key={c.criterion} className="flex items-center justify-between text-xs">
                      <span className="text-foreground truncate">{c.criterion}</span>
                      <span className={`inline-flex items-center gap-1 tabular-nums ${c.needs_calibration ? 'text-warning font-medium' : 'text-muted-foreground'}`}>
                        {c.needs_calibration && <AlertTriangle size={11} />}Δ {c.mean_spread}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1.5">Reviewer norming (vs panel mean {calibration.panel_mean})</p>
              {calibration.reviewer_drift.length === 0 ? (
                <p className="text-xs text-muted-foreground">No scored reviewers yet.</p>
              ) : (
                <div className="space-y-1">
                  {calibration.reviewer_drift.slice(0, 6).map(r => (
                    <div key={r.reviewer_id} className="flex items-center justify-between text-xs">
                      <span className="text-foreground truncate">{r.reviewer_name}</span>
                      <Badge variant={r.tendency === 'aligned' ? 'success' : r.tendency === 'lenient' ? 'info' : 'warning'}>
                        {r.tendency} {r.delta_vs_panel > 0 ? '+' : ''}{r.delta_vs_panel}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
          <div className="border-t border-border pt-2 text-xs text-muted-foreground">
            Test-optional outcomes — submitters: {pctRate(calibration.test_optional_cohort.submitters.admit_rate)} admit ({calibration.test_optional_cohort.submitters.n}) ·
            {' '}non-submitters: {pctRate(calibration.test_optional_cohort.non_submitters.admit_rate)} admit ({calibration.test_optional_cohort.non_submitters.n}).
            {' '}{calibration.test_optional_cohort.guardrail}
          </div>
        </Card>
      )}

      {/* Application picker */}
      {selectedProgram && (
        <Card className="p-4">
          <p className="text-sm font-medium text-foreground mb-2">Select 2+ applicants to compare:</p>
          {appsQ.isLoading ? (
            <Skeleton className="h-20" />
          ) : appsQ.isError ? (
            <QueryError variant="inline" detail="We couldn't load this program's applicants." onRetry={() => appsQ.refetch()} />
          ) : allApps.length === 0 ? (
            <p className="text-sm text-muted-foreground">No applications for this program.</p>
          ) : (
            <>
              <div className="flex flex-wrap gap-2 mb-3">
                <Button variant="tertiary" size="sm" onClick={selectAll}>Select all ({allApps.length})</Button>
                {selectedIds.length > 0 && (
                  <Button variant="ghost" size="sm" onClick={clearSelection}>Clear</Button>
                )}
              </div>
              <div className="flex flex-wrap gap-2">
              {allApps.map(app => (
                <button
                  key={app.id}
                  onClick={() => toggleApp(app.id)}
                  className={`px-3 py-1.5 rounded-lg border text-sm transition-all ${
                    selectedIds.includes(app.id)
                      ? 'bg-secondary/10 border-secondary/40 text-secondary font-medium'
                      : 'bg-card border-border text-muted-foreground hover:border-secondary/40'
                  }`}
                >
                  {applicantLabel(app)} {app.match_score != null && `(${formatScore(app.match_score)})`}
                </button>
              ))}
              </div>
            </>
          )}
        </Card>
      )}

      {/* Comparison Table */}
      {selectedIds.length < 2 ? (
        <EmptyState icon={<Users size={40} />} title="Select applicants" description="Pick 2 or more applicants from the same program to see their side-by-side comparison." />
      ) : cohortQ.isLoading ? (
        <Skeleton className="h-80" />
      ) : cohortQ.isError ? (
        <QueryError detail="We couldn't load the comparison for these applicants." onRetry={() => cohortQ.refetch()} />
      ) : sorted.length === 0 ? (
        <EmptyState icon={<BarChart3 size={40} />} title="No data" description="No comparison data available for the selected applicants." />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="text-left px-3 py-2 font-medium text-muted-foreground sticky left-0 bg-muted/50 z-10">Field</th>
                {sorted.map(a => (
                  <th key={a.application_id} className="text-center px-4 py-2 font-medium text-foreground min-w-[140px]">
                    {a.student_name || a.student_id.slice(0, 8)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {/* Status */}
              <tr className="border-b">
                <td className="px-3 py-2 font-medium text-muted-foreground sticky left-0 bg-card">Status</td>
                {sorted.map(a => (
                  <td key={a.application_id} className="text-center px-4 py-2">
                    <Badge variant="info">{a.status ?? '—'}</Badge>
                  </td>
                ))}
              </tr>
              {/* Decision */}
              <tr className="border-b">
                <td className="px-3 py-2 font-medium text-muted-foreground sticky left-0 bg-card">Decision</td>
                {sorted.map(a => (
                  <td key={a.application_id} className="text-center px-4 py-2">
                    {a.decision ? (
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${DECISION_COLORS[a.decision] ?? ''}`}>{a.decision}</span>
                    ) : '—'}
                  </td>
                ))}
              </tr>
              {/* Match Score */}
              <tr className="border-b hover:bg-muted/40 cursor-pointer" onClick={() => toggleSort('match_score')}>
                <td className="px-3 py-2 font-medium text-muted-foreground sticky left-0 bg-card flex items-center gap-1">
                  Match Score <SortIcon col="match_score" />
                </td>
                {sorted.map(a => (
                  <td key={a.application_id} className="text-center px-4 py-2 font-mono">
                    {a.match_score != null ? formatScore(a.match_score) : '—'}
                  </td>
                ))}
              </tr>
              {/* Avg Rubric Score */}
              <tr className="border-b bg-secondary/5 hover:bg-secondary/10 cursor-pointer" onClick={() => toggleSort('avg_score')}>
                <td className="px-3 py-2 font-semibold text-foreground sticky left-0 bg-secondary/5 flex items-center gap-1">
                  Avg Rubric Score <SortIcon col="avg_score" />
                </td>
                {sorted.map(a => (
                  <td key={a.application_id} className="text-center px-4 py-2 font-bold text-foreground">
                    {a.avg_score != null ? a.avg_score.toFixed(1) : '—'}
                  </td>
                ))}
              </tr>
              {/* Per-criterion scores */}
              {allCriteria.length > 0 && (
                <>
                  <tr className="border-b cursor-pointer hover:bg-muted/40" onClick={() => setExpandedCriteria(expandedCriteria ? null : 'all')}>
                    <td colSpan={sorted.length + 1} className="px-3 py-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      {expandedCriteria ? '▼' : '▶'} Rubric Criteria ({allCriteria.length})
                    </td>
                  </tr>
                  {expandedCriteria && allCriteria.map(criterion => (
                    <tr key={criterion} className="border-b">
                      <td className="px-3 py-1.5 text-muted-foreground text-xs pl-6 sticky left-0 bg-card">{criterion}</td>
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
                <td className="px-3 py-2 font-medium text-muted-foreground sticky left-0 bg-card">Completeness</td>
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
                <td className="px-3 py-2 font-medium text-muted-foreground sticky left-0 bg-card">GPA</td>
                {sorted.map(a => (
                  <td key={a.application_id} className="text-center px-4 py-2 font-mono">
                    {a.gpa != null ? a.gpa.toFixed(2) : '—'}
                  </td>
                ))}
              </tr>
              {/* Nationality */}
              <tr className="border-b">
                <td className="px-3 py-2 font-medium text-muted-foreground sticky left-0 bg-card">Nationality</td>
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

  if (embedded) return inner
  return <div className="p-6">{inner}</div>
}

function pctRate(r: number | null): string {
  return r == null ? '—' : `${Math.round(r * 100)}%`
}
