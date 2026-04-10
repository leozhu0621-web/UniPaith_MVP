import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listMyApplications, respondToOffer } from '../../api/applications'
import { getProgram } from '../../api/programs'
import { comparePrograms } from '../../api/saved-lists'
import { getProfile } from '../../api/students'
import { getMatches } from '../../api/matching'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Badge from '../../components/ui/Badge'
import EmptyState from '../../components/ui/EmptyState'
import { SkeletonCard } from '../../components/ui/Skeleton'
import { showToast } from '../../stores/toast-store'
import { formatCurrency, formatDate, formatPercent, formatScore } from '../../utils/format'
import { DEGREE_LABELS, DELIVERY_FORMAT_LABELS, CAMPUS_SETTING_LABELS, TIER_LABELS } from '../../utils/constants'
import { Scale, Sparkles, AlertTriangle, Check, X, Clock, ArrowUp, ArrowDown, Minus } from 'lucide-react'
import type { Application, Program, MatchResult, ComparisonResponse } from '../../types'

type DecisionState = 'thinking' | 'accepted' | 'declined'

function bestValue(values: (number | null | undefined)[], higher = true) {
  const nums = values.filter((v): v is number => v != null)
  if (nums.length === 0) return null
  return higher ? Math.max(...nums) : Math.min(...nums)
}

function ValueIndicator({ value, best }: { value: number | null | undefined; best: number | null }) {
  if (value == null || best == null) return <Minus size={12} className="text-gray-300" />
  if (value === best) return <ArrowUp size={12} className="text-green-500" />
  return <ArrowDown size={12} className="text-red-400" />
}

export default function DecisionComparisonPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null)
  const [decisionStates, setDecisionStates] = useState<Record<string, DecisionState>>({})
  const [respondingId, setRespondingId] = useState<string | null>(null)

  const { data: applications, isLoading: appsLoading } = useQuery({
    queryKey: ['my-applications'],
    queryFn: listMyApplications,
  })
  const { data: profile } = useQuery({
    queryKey: ['profile'],
    queryFn: getProfile,
  })
  const { data: matches } = useQuery({
    queryKey: ['matches'],
    queryFn: () => getMatches(),
  })

  const appList: Application[] = Array.isArray(applications) ? applications : []

  const matchLookup = useMemo(() => {
    const lookup: Record<string, MatchResult> = {}
    const list: MatchResult[] = Array.isArray(matches) ? matches : []
    list.forEach(m => { lookup[m.program_id] = m })
    return lookup
  }, [matches])

  const offeredApps = useMemo(
    () => appList.filter(a => a.decision === 'admitted' || a.decision === 'waitlisted'),
    [appList],
  )

  const programQueries = useMemo(() => {
    const ids: string[] = []
    selected.forEach(appId => {
      const app = offeredApps.find(a => a.id === appId)
      if (app?.program_id) ids.push(app.program_id)
    })
    return ids
  }, [selected, offeredApps])

  const programQueryKey = useMemo(() => [...programQueries].sort().join(','), [programQueries])

  const { data: programDetails } = useQuery({
    queryKey: ['program-details', programQueryKey],
    queryFn: () => Promise.all(programQueries.map(id => getProgram(id).catch(() => null))),
    enabled: programQueries.length > 0,
  })

  const programMap = useMemo(() => {
    const map: Record<string, Program> = {}
    if (programDetails) {
      programDetails.forEach((p: Program | null) => { if (p) map[p.id] = p })
    }
    return map
  }, [programDetails])

  const compareMut = useMutation({
    mutationFn: (ids: string[]) => comparePrograms(ids),
    onSuccess: (data) => setComparison(data),
    onError: () => showToast('Could not generate comparison', 'error'),
  })

  const offerMut = useMutation({
    mutationFn: ({ appId, response }: { appId: string; response: string }) =>
      respondToOffer(appId, response),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-applications'] })
      showToast('Response submitted', 'success')
      setRespondingId(null)
    },
    onError: () => showToast('Failed to submit response', 'error'),
  })

  const toggle = (id: string) => {
    const next = new Set(selected)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    setSelected(next)
  }

  const handleDecision = (appId: string, decision: DecisionState) => {
    if (decision === 'thinking') {
      setDecisionStates(prev => ({ ...prev, [appId]: 'thinking' }))
      return
    }
    setRespondingId(appId)
    setDecisionStates(prev => ({ ...prev, [appId]: decision }))
    offerMut.mutate({ appId, response: decision })
  }

  const constraints = useMemo(() => {
    const prefs = profile?.preferences
    if (!prefs) return []
    const flags: { appId: string; message: string }[] = []

    offeredApps.forEach(app => {
      if (!selected.has(app.id)) return
      const program = programMap[app.program_id]
      if (!program) return

      if (prefs.budget_max != null && program.tuition != null && program.tuition > prefs.budget_max) {
        flags.push({
          appId: app.id,
          message: `${program.program_name} tuition (${formatCurrency(program.tuition)}) exceeds your budget max (${formatCurrency(prefs.budget_max)})`,
        })
      }

      if (prefs.dealbreakers?.length) {
        prefs.dealbreakers.forEach((db: string) => {
          const lc = db.toLowerCase()
          if (lc.includes('online') && program.delivery_format === 'online') {
            flags.push({ appId: app.id, message: `${program.program_name}: your dealbreaker "${db}" may conflict with this program's online format` })
          }
          if (lc.includes('rural') && program.campus_setting === 'rural') {
            flags.push({ appId: app.id, message: `${program.program_name}: your dealbreaker "${db}" may conflict with this program's rural setting` })
          }
        })
      }
    })

    return flags
  }, [profile, offeredApps, selected, programMap])

  const selectedApps = useMemo(
    () => offeredApps.filter(a => selected.has(a.id)),
    [offeredApps, selected],
  )

  if (appsLoading) {
    return (
      <div className="p-6 space-y-4">
        {Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)}
      </div>
    )
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-brand-slate-100 flex items-center justify-center">
          <Scale size={20} className="text-brand-slate-600" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold">Decision Center</h1>
          <p className="text-sm text-gray-500">Compare offers side-by-side and make your enrollment decision</p>
        </div>
      </div>

      {offeredApps.length === 0 ? (
        <EmptyState
          icon={<Scale size={48} />}
          title="No offers to compare yet"
          description="Once you receive admission decisions, they'll appear here for comparison."
          action={{ label: 'View Applications', onClick: () => navigate('/s/applications') }}
        />
      ) : (
        <>
          <Card className="p-4 mb-6">
            <h2 className="font-medium text-sm mb-3">Select offers to compare</h2>
            <div className="space-y-2">
              {offeredApps.map(app => (
                <label key={app.id} className="flex items-center gap-3 p-3 rounded-lg border border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors">
                  <input
                    type="checkbox"
                    checked={selected.has(app.id)}
                    onChange={() => toggle(app.id)}
                    className="rounded"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm">{app.program?.program_name || 'Program'}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <Badge variant={app.decision === 'admitted' ? 'success' : 'warning'} size="sm">
                        {app.decision === 'admitted' ? 'Admitted' : 'Waitlisted'}
                      </Badge>
                      {matchLookup[app.program_id] && (
                        <span className="text-xs text-gray-500">
                          Match: {formatScore(matchLookup[app.program_id].match_score)}
                        </span>
                      )}
                    </div>
                  </div>
                  {app.program?.tuition != null && (
                    <span className="text-sm text-gray-500">{formatCurrency(app.program.tuition)}</span>
                  )}
                </label>
              ))}
            </div>
            {selected.size >= 2 && (
              <div className="flex gap-2 mt-3">
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => compareMut.mutate(programQueries)}
                  loading={compareMut.isPending}
                >
                  <Sparkles size={14} className="mr-1" /> AI Analysis
                </Button>
              </div>
            )}
          </Card>

          {constraints.length > 0 && (
            <Card className="p-4 mb-6 border-l-4 border-l-amber-400">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle size={16} className="text-amber-500" />
                <h3 className="font-medium text-sm text-amber-800">Constraint Flags</h3>
              </div>
              <ul className="space-y-1">
                {constraints.map((c, i) => (
                  <li key={i} className="text-sm text-amber-700 flex items-start gap-2">
                    <span className="mt-0.5 flex-shrink-0">-</span>
                    <span>{c.message}</span>
                  </li>
                ))}
              </ul>
            </Card>
          )}

          {selectedApps.length >= 2 && (
            <Card className="mb-6 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-gray-50">
                      <th className="text-left py-3 px-4 text-gray-500 font-medium w-40">Feature</th>
                      {selectedApps.map(app => (
                        <th key={app.id} className="text-left py-3 px-4 font-semibold">
                          <div>
                            <p className="truncate max-w-[180px]">{app.program?.program_name || 'Program'}</p>
                            <Badge variant={app.decision === 'admitted' ? 'success' : 'warning'} size="sm" className="mt-1">
                              {app.decision}
                            </Badge>
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(() => {
                      const values = selectedApps.map(a => programMap[a.program_id]?.tuition ?? a.program?.tuition)
                      const best = bestValue(values, false)
                      return (
                        <tr className="border-b">
                          <td className="py-3 px-4 text-gray-500 font-medium">Tuition</td>
                          {selectedApps.map((a, i) => (
                            <td key={a.id} className={`py-3 px-4 ${values[i] === best && best != null ? 'bg-green-50' : ''}`}>
                              <div className="flex items-center gap-2">
                                <span>{formatCurrency(values[i])}</span>
                                <ValueIndicator value={values[i]} best={best} />
                              </div>
                            </td>
                          ))}
                        </tr>
                      )
                    })()}

                    {(() => {
                      const fees = selectedApps.map(a => {
                        const cd = programMap[a.program_id]?.cost_data
                        return cd?.fees ?? cd?.total_fees ?? null
                      })
                      if (!fees.some(f => f != null)) return null
                      const best = bestValue(fees, false)
                      return (
                        <tr className="border-b">
                          <td className="py-3 px-4 text-gray-500">Fees</td>
                          {selectedApps.map((a, i) => (
                            <td key={a.id} className={`py-3 px-4 ${fees[i] === best && best != null ? 'bg-green-50' : ''}`}>
                              <div className="flex items-center gap-2">
                                <span>{fees[i] != null ? formatCurrency(fees[i]) : '--'}</span>
                                <ValueIndicator value={fees[i]} best={best} />
                              </div>
                            </td>
                          ))}
                        </tr>
                      )
                    })()}

                    {(() => {
                      const totals = selectedApps.map(a => {
                        const p = programMap[a.program_id]
                        const tuition = p?.tuition ?? a.program?.tuition
                        const fees = p?.cost_data?.fees ?? p?.cost_data?.total_fees ?? 0
                        return tuition != null ? tuition + (fees ?? 0) : null
                      })
                      const best = bestValue(totals, false)
                      return (
                        <tr className="border-b bg-gray-50">
                          <td className="py-3 px-4 text-gray-500 font-medium">Total Cost</td>
                          {selectedApps.map((a, i) => (
                            <td key={a.id} className={`py-3 px-4 font-semibold ${totals[i] === best && best != null ? 'bg-green-50' : ''}`}>
                              <div className="flex items-center gap-2">
                                <span>{formatCurrency(totals[i])}</span>
                                <ValueIndicator value={totals[i]} best={best} />
                              </div>
                            </td>
                          ))}
                        </tr>
                      )
                    })()}

                    {(() => {
                      const scores = selectedApps.map(a => matchLookup[a.program_id]?.match_score)
                      const best = bestValue(scores, true)
                      return (
                        <tr className="border-b">
                          <td className="py-3 px-4 text-gray-500 font-medium">Fit Score</td>
                          {selectedApps.map((a, i) => {
                            const m = matchLookup[a.program_id]
                            const tierInfo = m ? TIER_LABELS[m.match_tier] : null
                            return (
                              <td key={a.id} className={`py-3 px-4 ${scores[i] === best && best != null ? 'bg-green-50' : ''}`}>
                                {m ? (
                                  <div className="flex items-center gap-2">
                                    <span className="font-bold">{formatScore(m.match_score)}</span>
                                    {tierInfo && <Badge variant={tierInfo.color as any} size="sm">{tierInfo.label}</Badge>}
                                    <ValueIndicator value={scores[i]} best={best} />
                                  </div>
                                ) : '--'}
                              </td>
                            )
                          })}
                        </tr>
                      )
                    })()}

                    {(() => {
                      const salaries = selectedApps.map(a => {
                        const p = programMap[a.program_id]
                        return p?.outcomes_data?.median_salary ?? (a.program as any)?.median_salary ?? null
                      })
                      const best = bestValue(salaries, true)
                      return (
                        <tr className="border-b">
                          <td className="py-3 px-4 text-gray-500">Median Salary</td>
                          {selectedApps.map((a, i) => (
                            <td key={a.id} className={`py-3 px-4 ${salaries[i] === best && best != null ? 'bg-green-50' : ''}`}>
                              <div className="flex items-center gap-2">
                                <span>{salaries[i] != null ? formatCurrency(salaries[i]) : '--'}</span>
                                <ValueIndicator value={salaries[i]} best={best} />
                              </div>
                            </td>
                          ))}
                        </tr>
                      )
                    })()}

                    {(() => {
                      const rates = selectedApps.map(a => {
                        const p = programMap[a.program_id]
                        return p?.outcomes_data?.employment_rate ?? (a.program as any)?.employment_rate ?? null
                      })
                      const best = bestValue(rates, true)
                      return (
                        <tr className="border-b">
                          <td className="py-3 px-4 text-gray-500">Employment Rate</td>
                          {selectedApps.map((a, i) => (
                            <td key={a.id} className={`py-3 px-4 ${rates[i] === best && best != null ? 'bg-green-50' : ''}`}>
                              <div className="flex items-center gap-2">
                                <span>{rates[i] != null ? formatPercent(rates[i], 1) : '--'}</span>
                                <ValueIndicator value={rates[i]} best={best} />
                              </div>
                            </td>
                          ))}
                        </tr>
                      )
                    })()}

                    <tr className="border-b">
                      <td className="py-3 px-4 text-gray-500">Location</td>
                      {selectedApps.map(a => {
                        const p = programMap[a.program_id]
                        const setting = p?.campus_setting ? CAMPUS_SETTING_LABELS[p.campus_setting] ?? p.campus_setting : null
                        return (
                          <td key={a.id} className="py-3 px-4">
                            {setting || '--'}
                          </td>
                        )
                      })}
                    </tr>

                    <tr className="border-b">
                      <td className="py-3 px-4 text-gray-500">Format</td>
                      {selectedApps.map(a => {
                        const p = programMap[a.program_id]
                        const fmt = p?.delivery_format ? DELIVERY_FORMAT_LABELS[p.delivery_format] ?? p.delivery_format : null
                        return (
                          <td key={a.id} className="py-3 px-4">
                            {fmt || '--'}
                          </td>
                        )
                      })}
                    </tr>

                    {(() => {
                      const durations = selectedApps.map(a => programMap[a.program_id]?.duration_months ?? a.program?.duration_months)
                      const best = bestValue(durations, false)
                      return (
                        <tr className="border-b">
                          <td className="py-3 px-4 text-gray-500">Duration</td>
                          {selectedApps.map((a, i) => (
                            <td key={a.id} className={`py-3 px-4 ${durations[i] === best && best != null ? 'bg-green-50' : ''}`}>
                              <div className="flex items-center gap-2">
                                <span>{durations[i] != null ? `${durations[i]} months` : '--'}</span>
                                <ValueIndicator value={durations[i]} best={best} />
                              </div>
                            </td>
                          ))}
                        </tr>
                      )
                    })()}

                    <tr className="border-b">
                      <td className="py-3 px-4 text-gray-500">Degree</td>
                      {selectedApps.map(a => {
                        const p = programMap[a.program_id]
                        const dt = p?.degree_type ?? a.program?.degree_type
                        return (
                          <td key={a.id} className="py-3 px-4">
                            {dt ? <Badge variant="info" size="sm">{DEGREE_LABELS[dt] ?? dt}</Badge> : '--'}
                          </td>
                        )
                      })}
                    </tr>

                    <tr className="border-b bg-gray-50">
                      <td className="py-3 px-4 text-gray-500 font-medium">Response Deadline</td>
                      {selectedApps.map(a => (
                        <td key={a.id} className="py-3 px-4">
                          {a.program?.application_deadline ? formatDate(a.program.application_deadline) : '--'}
                        </td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {comparison?.ai_analysis && (
            <Card className="p-5 mb-6">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles size={16} className="text-brand-slate-600" />
                <h3 className="font-medium">AI Comparison Analysis</h3>
              </div>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{comparison.ai_analysis}</p>
            </Card>
          )}

          {selectedApps.length > 0 && (
            <div className="space-y-3">
              <h2 className="font-medium text-sm text-gray-700">Enrollment Decisions</h2>
              {selectedApps.map(app => {
                const state = decisionStates[app.id]
                const isResponding = respondingId === app.id && offerMut.isPending
                return (
                  <Card key={app.id} className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-sm">{app.program?.program_name || 'Program'}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant={app.decision === 'admitted' ? 'success' : 'warning'} size="sm">
                            {app.decision}
                          </Badge>
                          {state && (
                            <Badge
                              variant={state === 'accepted' ? 'success' : state === 'declined' ? 'danger' : 'neutral'}
                              size="sm"
                            >
                              {state === 'accepted' ? 'Accepted' : state === 'declined' ? 'Declined' : 'Thinking'}
                            </Badge>
                          )}
                        </div>
                      </div>
                      {app.decision === 'admitted' && (
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleDecision(app.id, 'thinking')}
                            disabled={isResponding}
                            className={state === 'thinking' ? 'ring-2 ring-gray-300' : ''}
                          >
                            <Clock size={14} className="mr-1" /> Thinking
                          </Button>
                          <Button
                            size="sm"
                            onClick={() => handleDecision(app.id, 'accepted')}
                            loading={isResponding && state === 'accepted'}
                            disabled={isResponding}
                          >
                            <Check size={14} className="mr-1" /> Accept
                          </Button>
                          <Button
                            size="sm"
                            variant="danger"
                            onClick={() => handleDecision(app.id, 'declined')}
                            loading={isResponding && state === 'declined'}
                            disabled={isResponding}
                          >
                            <X size={14} className="mr-1" /> Decline
                          </Button>
                        </div>
                      )}
                    </div>
                  </Card>
                )
              })}
            </div>
          )}
        </>
      )}
    </div>
  )
}
