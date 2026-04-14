import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listTestScores, createTestScore, updateTestScore, deleteTestScore } from '../../api/students'
import { listSaved } from '../../api/saved-lists'
import { listMyApplications } from '../../api/applications'
import { getProgram } from '../../api/programs'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import Tabs from '../../components/ui/Tabs'
import EmptyState from '../../components/ui/EmptyState'
import { SkeletonCard } from '../../components/ui/Skeleton'
import { useToastStore } from '../../stores/toast-store'
import { formatDate } from '../../utils/format'
import { TEST_TYPES } from '../../utils/constants'
import { GraduationCap, Plus, Pencil, Trash2, CheckCircle, XCircle, Send } from 'lucide-react'

const SUB_SCORE_DEFS: Record<string, { key: string; label: string; max: number }[]> = {
  GRE: [
    { key: 'verbal', label: 'Verbal', max: 170 },
    { key: 'quantitative', label: 'Quantitative', max: 170 },
    { key: 'writing', label: 'Analytical Writing', max: 6 },
  ],
  GMAT: [
    { key: 'verbal', label: 'Verbal', max: 60 },
    { key: 'quantitative', label: 'Quantitative', max: 60 },
    { key: 'integrated', label: 'Integrated Reasoning', max: 8 },
    { key: 'writing', label: 'Analytical Writing', max: 6 },
  ],
  TOEFL: [
    { key: 'reading', label: 'Reading', max: 30 },
    { key: 'listening', label: 'Listening', max: 30 },
    { key: 'speaking', label: 'Speaking', max: 30 },
    { key: 'writing', label: 'Writing', max: 30 },
  ],
  IELTS: [
    { key: 'reading', label: 'Reading', max: 9 },
    { key: 'listening', label: 'Listening', max: 9 },
    { key: 'speaking', label: 'Speaking', max: 9 },
    { key: 'writing', label: 'Writing', max: 9 },
  ],
  SAT: [
    { key: 'reading_writing', label: 'Reading & Writing', max: 800 },
    { key: 'math', label: 'Math', max: 800 },
  ],
  ACT: [
    { key: 'english', label: 'English', max: 36 },
    { key: 'math', label: 'Math', max: 36 },
    { key: 'reading', label: 'Reading', max: 36 },
    { key: 'science', label: 'Science', max: 36 },
  ],
  LSAT: [],
  MCAT: [
    { key: 'chem_phys', label: 'Chem/Phys', max: 132 },
    { key: 'cars', label: 'CARS', max: 132 },
    { key: 'bio_biochem', label: 'Bio/Biochem', max: 132 },
    { key: 'psych_soc', label: 'Psych/Soc', max: 132 },
  ],
  DUOLINGO: [],
  AP: [],
  IB: [],
}

const MAX_SCORES: Record<string, number> = {
  GRE: 340, GMAT: 800, TOEFL: 120, IELTS: 9, SAT: 1600, ACT: 36,
  LSAT: 180, MCAT: 528, DUOLINGO: 160, AP: 5, IB: 45,
}

const TEST_BADGE_VARIANT: Record<string, 'info' | 'success' | 'warning' | 'neutral'> = {
  GRE: 'info', GMAT: 'info', TOEFL: 'success', IELTS: 'success',
  SAT: 'warning', ACT: 'warning', LSAT: 'info', MCAT: 'info',
  DUOLINGO: 'success', AP: 'neutral', IB: 'neutral',
}

interface ScoreForm {
  test_type: string
  score: string
  sub_scores: Record<string, string>
  test_date: string
}
const EMPTY_FORM: ScoreForm = { test_type: 'GRE', score: '', sub_scores: {}, test_date: '' }

function parseRequirements(program: any) {
  const reqs: { test: string; required: boolean; minScore?: number }[] = []
  const raw = program?.requirements ?? program?.admission_requirements
  if (typeof raw === 'string') {
    const lower = raw.toLowerCase()
    for (const t of TEST_TYPES) {
      if (lower.includes(t.toLowerCase())) {
        reqs.push({ test: t, required: lower.includes(`${t.toLowerCase()} required`) || lower.includes(`require ${t.toLowerCase()}`) })
      }
    }
  } else if (raw && typeof raw === 'object') {
    for (const t of TEST_TYPES) {
      const key = t.toLowerCase()
      if (raw[key] || raw[`${key}_required`]) {
        reqs.push({
          test: t,
          required: raw[`${key}_required`] !== false,
          minScore: typeof raw[key] === 'number' ? raw[key] : raw[`min_${key}`],
        })
      }
    }
  }
  // Fallback: infer English proficiency as optional if no requirements found
  if (reqs.length === 0 && program?.institution_country && !['China', 'Japan', 'South Korea'].includes(program.institution_country)) {
    reqs.push({ test: 'TOEFL', required: false }, { test: 'IELTS', required: false })
  }
  return reqs
}

function programName(p: any) { return p.program_name || p.name || 'Program' }
function institutionName(p: any) { return p.institution_name || p.institution || '' }

export default function TestScorePage() {
  const qc = useQueryClient()
  const addToast = useToastStore(s => s.addToast)

  const { data: scores, isLoading: scoresLoading } = useQuery({ queryKey: ['test-scores'], queryFn: listTestScores })
  const { data: saved } = useQuery({ queryKey: ['saved-programs'], queryFn: listSaved })
  const { data: applications } = useQuery({ queryKey: ['my-applications'], queryFn: listMyApplications })

  const [tab, setTab] = useState('scores')
  const [modalOpen, setModalOpen] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState<ScoreForm>(EMPTY_FORM)
  const [submissionSets, setSubmissionSets] = useState<Record<string, Set<string>>>({})

  const invalidate = () => qc.invalidateQueries({ queryKey: ['test-scores'] })
  const createMut = useMutation({
    mutationFn: (data: any) => createTestScore(data),
    onSuccess: () => { invalidate(); setModalOpen(false); addToast('Score added', 'success') },
    onError: () => addToast('Failed to add score', 'error'),
  })
  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => updateTestScore(id, data),
    onSuccess: () => { invalidate(); setModalOpen(false); setEditingId(null); addToast('Score updated', 'success') },
    onError: () => addToast('Failed to update score', 'error'),
  })
  const deleteMut = useMutation({
    mutationFn: deleteTestScore,
    onSuccess: () => { invalidate(); addToast('Score deleted', 'success') },
    onError: () => addToast('Failed to delete score', 'error'),
  })

  const allPrograms = useMemo(() => {
    const sl: any[] = Array.isArray(saved) ? saved : []
    const al: any[] = Array.isArray(applications) ? applications : []
    const seen = new Set<string>()
    const result: any[] = []
    for (const s of sl) {
      if (s.program && !seen.has(s.program_id)) {
        seen.add(s.program_id)
        result.push({ id: s.program_id, ...s.program })
      }
    }
    for (const a of al) {
      if (a.program && !seen.has(a.program_id)) {
        seen.add(a.program_id)
        result.push({ id: a.program_id, ...a.program })
      }
    }
    return result
  }, [saved, applications])

  // Fetch full program details for requirements
  const programQueries = useQuery({
    queryKey: ['program-details-batch', allPrograms.map((p: any) => p.id)],
    queryFn: async () => {
      if (allPrograms.length === 0) return []
      const results = await Promise.allSettled(allPrograms.map((p: any) => getProgram(p.id)))
      return results.map((r, i) => r.status === 'fulfilled' ? r.value : allPrograms[i])
    },
    enabled: allPrograms.length > 0,
  })

  const programDetails: any[] = programQueries.data ?? allPrograms
  const scoreList: any[] = Array.isArray(scores) ? scores : []

  const openAdd = () => { setEditingId(null); setForm(EMPTY_FORM); setModalOpen(true) }
  const openEdit = (s: any) => {
    setEditingId(s.id)
    setForm({
      test_type: s.test_type,
      score: String(s.total_score ?? ''),
      sub_scores: Object.fromEntries(Object.entries(s.section_scores ?? {}).map(([k, v]) => [k, String(v)])),
      test_date: s.test_date ? s.test_date.slice(0, 10) : '',
    })
    setModalOpen(true)
  }
  const handleSave = () => {
    const numericSubs: Record<string, number> = {}
    for (const [k, v] of Object.entries(form.sub_scores)) {
      if (v) numericSubs[k] = Number(v)
    }
    const payload = {
      test_type: form.test_type,
      total_score: form.score ? Number(form.score) : null,
      section_scores: Object.keys(numericSubs).length > 0 ? numericSubs : null,
      test_date: form.test_date || null,
    }
    if (editingId) updateMut.mutate({ id: editingId, data: payload })
    else createMut.mutate(payload)
  }

  const toggleSubmission = (programId: string, scoreId: string) => {
    setSubmissionSets(prev => {
      const next = { ...prev }
      const set = new Set(prev[programId] ?? [])
      if (set.has(scoreId)) set.delete(scoreId)
      else set.add(scoreId)
      next[programId] = set
      return next
    })
  }

  const hasScore = (testType: string) => scoreList.some((s: any) => s.test_type === testType)
  const activeSubScoreDefs = SUB_SCORE_DEFS[form.test_type] ?? []

  const tabItems = [
    { id: 'scores', label: 'My Scores', count: scoreList.length },
    { id: 'requirements', label: 'Program Requirements', count: programDetails.length },
    { id: 'submission', label: 'Submission Sets' },
    { id: 'comparison', label: 'Score Comparison' },
  ]

  if (scoresLoading) {
    return (
      <div className="p-6 max-w-5xl mx-auto space-y-4">
        {Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)}
      </div>
    )
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <GraduationCap size={28} className="text-brand-slate-600" />
          <div>
            <h1 className="text-2xl font-semibold">Test Scores</h1>
            <p className="text-sm text-gray-500">Manage scores, check program requirements, and build submission sets.</p>
          </div>
        </div>
        <Button onClick={openAdd} size="sm">
          <Plus size={14} className="mr-1" /> Add Score
        </Button>
      </div>

      <Tabs tabs={tabItems} activeTab={tab} onChange={setTab} />

      <div className="mt-6">
        {tab === 'scores' && (
          scoreList.length === 0 ? (
            <EmptyState
              icon={<GraduationCap size={48} />}
              title="No test scores yet"
              description="Add your standardized test scores to track requirements and build submission sets."
              action={{ label: 'Add Score', onClick: openAdd }}
            />
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {scoreList.map((s: any) => {
                const defs = SUB_SCORE_DEFS[s.test_type] ?? []
                const max = MAX_SCORES[s.test_type]
                const pct = max && s.total_score ? Math.min(100, Math.round((s.total_score / max) * 100)) : null
                return (
                  <Card key={s.id} className="p-5 flex flex-col gap-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant={TEST_BADGE_VARIANT[s.test_type] ?? 'neutral'}>{s.test_type}</Badge>
                        <span className="text-xl font-bold">{s.total_score ?? '\u2014'}</span>
                        {max && <span className="text-xs text-gray-400">/ {max}</span>}
                      </div>
                      <div className="flex gap-1">
                        <button onClick={() => openEdit(s)} className="p-1.5 rounded hover:bg-gray-100" title="Edit">
                          <Pencil size={14} className="text-gray-500" />
                        </button>
                        <button onClick={() => deleteMut.mutate(s.id)} className="p-1.5 rounded hover:bg-gray-100" title="Delete">
                          <Trash2 size={14} className="text-gray-400" />
                        </button>
                      </div>
                    </div>

                    {pct !== null && (
                      <div className="h-1.5 rounded-full bg-gray-100 overflow-hidden">
                        <div className="h-full rounded-full bg-brand-slate-500 transition-all" style={{ width: `${pct}%` }} />
                      </div>
                    )}

                    {defs.length > 0 && s.section_scores && (
                      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                        {defs.map(d => (
                          <div key={d.key} className="flex justify-between">
                            <span className="text-gray-500">{d.label}</span>
                            <span className="font-medium">{s.section_scores?.[d.key] ?? '\u2014'}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {s.test_date && (
                      <p className="text-xs text-gray-400">Taken {formatDate(s.test_date)}</p>
                    )}
                  </Card>
                )
              })}
            </div>
          )
        )}

        {tab === 'requirements' && (
          programDetails.length === 0 ? (
            <EmptyState
              icon={<GraduationCap size={48} />}
              title="No programs yet"
              description="Save or apply to programs to see their test score requirements."
            />
          ) : (
            <div className="space-y-4">
              {programDetails.map((p: any) => {
                const reqs = parseRequirements(p)
                return (
                  <Card key={p.id} className="p-5">
                    <h3 className="font-semibold text-sm mb-1">{programName(p)}</h3>
                    <p className="text-xs text-gray-500 mb-3">{institutionName(p)}</p>

                    {reqs.length === 0 ? (
                      <p className="text-xs text-gray-400 italic">No specific test requirements found for this program.</p>
                    ) : (
                      <div className="space-y-2">
                        {reqs.map(r => {
                          const has = hasScore(r.test)
                          const best = scoreList.filter((s: any) => s.test_type === r.test).sort((a: any, b: any) => (b.score ?? 0) - (a.score ?? 0))[0]
                          const meetsMin = r.minScore && best?.score ? best.score >= r.minScore : true
                          return (
                            <div key={r.test} className="flex items-center justify-between text-sm">
                              <div className="flex items-center gap-2">
                                {has && meetsMin ? (
                                  <CheckCircle size={16} className="text-green-500" />
                                ) : (
                                  <XCircle size={16} className="text-red-400" />
                                )}
                                <span className="font-medium">{r.test}</span>
                                <Badge variant={r.required ? 'danger' : 'neutral'} size="sm">
                                  {r.required ? 'Required' : 'Optional'}
                                </Badge>
                              </div>
                              <div className="text-right text-xs text-gray-500">
                                {r.minScore && <span className="mr-2">Min: {r.minScore}</span>}
                                {best ? <span className="font-medium text-gray-700">Your score: {best.score}</span> : <span className="text-gray-400">No score</span>}
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </Card>
                )
              })}
            </div>
          )
        )}

        {tab === 'submission' && (
          scoreList.length === 0 || programDetails.length === 0 ? (
            <EmptyState
              icon={<Send size={48} />}
              title="Add scores and save programs first"
              description="You need at least one test score and one saved/applied program to build submission sets."
            />
          ) : (
            <div className="space-y-6">
              {programDetails.map((p: any) => {
                const selected = submissionSets[p.id] ?? new Set<string>()
                return (
                  <Card key={p.id} className="p-5">
                    <h3 className="font-semibold text-sm mb-1">{programName(p)}</h3>
                    <p className="text-xs text-gray-500 mb-3">{institutionName(p)}</p>

                    <div className="space-y-2">
                      {scoreList.map((s: any) => (
                        <label key={s.id} className="flex items-center gap-3 text-sm cursor-pointer hover:bg-gray-50 rounded p-2 -mx-2">
                          <input
                            type="checkbox"
                            checked={selected.has(s.id)}
                            onChange={() => toggleSubmission(p.id, s.id)}
                            className="rounded border-gray-300 text-brand-slate-600 focus:ring-brand-slate-500"
                          />
                          <Badge variant={TEST_BADGE_VARIANT[s.test_type] ?? 'neutral'} size="sm">{s.test_type}</Badge>
                          <span className="font-medium">{s.total_score ?? '\u2014'}</span>
                          {s.test_date && <span className="text-xs text-gray-400 ml-auto">{formatDate(s.test_date)}</span>}
                        </label>
                      ))}
                    </div>

                    {selected.size > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-100">
                        <p className="text-xs text-gray-500 mb-1">Submission summary:</p>
                        <div className="flex flex-wrap gap-1.5">
                          {[...selected].map(sid => {
                            const sc = scoreList.find((s: any) => s.id === sid)
                            return sc ? (
                              <Badge key={sid} variant="info" size="sm">{sc.test_type}: {sc.score ?? '\u2014'}</Badge>
                            ) : null
                          })}
                        </div>
                      </div>
                    )}
                  </Card>
                )
              })}
            </div>
          )
        )}

        {tab === 'comparison' && (
          scoreList.length === 0 ? (
            <EmptyState
              icon={<GraduationCap size={48} />}
              title="No scores to compare"
              description="Add test scores to see how they compare against program requirements."
              action={{ label: 'Add Score', onClick: openAdd }}
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-3 text-xs font-medium text-gray-500 uppercase">Program</th>
                    {scoreList.map((s: any) => (
                      <th key={s.id} className="text-center py-3 px-3 text-xs font-medium text-gray-500 uppercase">
                        {s.test_type}
                        <div className="text-sm font-bold text-gray-900 mt-0.5">{s.total_score ?? '\u2014'}</div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {programDetails.length === 0 ? (
                    <tr>
                      <td colSpan={scoreList.length + 1} className="py-8 text-center text-gray-400 text-sm">
                        Save or apply to programs to compare scores.
                      </td>
                    </tr>
                  ) : (
                    programDetails.map((p: any) => {
                      const reqs = parseRequirements(p)
                      return (
                        <tr key={p.id} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="py-3 px-3">
                            <p className="font-medium text-sm">{programName(p)}</p>
                            <p className="text-xs text-gray-400">{institutionName(p)}</p>
                          </td>
                          {scoreList.map((s: any) => {
                            const req = reqs.find(r => r.test === s.test_type)
                            if (!req) {
                              return <td key={s.id} className="text-center py-3 px-3 text-gray-300">--</td>
                            }
                            const meets = req.minScore ? (s.total_score ?? 0) >= req.minScore : true
                            return (
                              <td key={s.id} className="text-center py-3 px-3">
                                <div className="flex flex-col items-center gap-0.5">
                                  {meets ? (
                                    <CheckCircle size={16} className="text-green-500" />
                                  ) : (
                                    <XCircle size={16} className="text-red-400" />
                                  )}
                                  {req.minScore && (
                                    <span className="text-[10px] text-gray-400">min {req.minScore}</span>
                                  )}
                                </div>
                              </td>
                            )
                          })}
                        </tr>
                      )
                    })
                  )}
                </tbody>
              </table>
            </div>
          )
        )}
      </div>

      <Modal isOpen={modalOpen} onClose={() => { setModalOpen(false); setEditingId(null) }} title={editingId ? 'Edit Score' : 'Add Test Score'}>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Test Type</label>
            <select
              value={form.test_type}
              onChange={e => setForm(f => ({ ...f, test_type: e.target.value, sub_scores: {} }))}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-slate-500"
            >
              {TEST_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Total Score {MAX_SCORES[form.test_type] && <span className="text-gray-400 font-normal">(max {MAX_SCORES[form.test_type]})</span>}
            </label>
            <input
              type="number"
              value={form.score}
              onChange={e => setForm(f => ({ ...f, score: e.target.value }))}
              placeholder="e.g. 320"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-slate-500"
            />
          </div>

          {activeSubScoreDefs.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Sub-Scores</label>
              <div className="grid grid-cols-2 gap-3">
                {activeSubScoreDefs.map(d => (
                  <div key={d.key}>
                    <label className="text-xs text-gray-500">{d.label} <span className="text-gray-300">(max {d.max})</span></label>
                    <input
                      type="number"
                      value={form.sub_scores[d.key] ?? ''}
                      onChange={e => setForm(f => ({ ...f, sub_scores: { ...f.sub_scores, [d.key]: e.target.value } }))}
                      className="w-full rounded-lg border border-gray-300 px-3 py-1.5 text-sm mt-0.5 focus:outline-none focus:ring-2 focus:ring-brand-slate-500"
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Test Date</label>
            <input
              type="date"
              value={form.test_date}
              onChange={e => setForm(f => ({ ...f, test_date: e.target.value }))}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-slate-500"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" size="sm" onClick={() => { setModalOpen(false); setEditingId(null) }}>
              Cancel
            </Button>
            <Button size="sm" onClick={handleSave} loading={createMut.isPending || updateMut.isPending}>
              {editingId ? 'Update' : 'Add Score'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
