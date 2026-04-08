import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Layers, Plus, Edit2, Trash2, ToggleLeft, ToggleRight, ChevronDown, ChevronUp } from 'lucide-react'
import { getSegments, createSegment, updateSegment, deleteSegment, getInstitutionPrograms, previewSegmentAudience } from '../../api/institutions'
import InstitutionPageHeader from '../../components/institution/InstitutionPageHeader'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import Input from '../../components/ui/Input'
import Select from '../../components/ui/Select'
import Textarea from '../../components/ui/Textarea'
import EmptyState from '../../components/ui/EmptyState'
import Skeleton from '../../components/ui/Skeleton'
import { showToast } from '../../stores/toast-store'
import { formatDate } from '../../utils/format'
import type { Segment, Program } from '../../types'

/* ------------------------------------------------------------------ */
/*  Criteria types                                                     */
/* ------------------------------------------------------------------ */

interface CriteriaState {
  statuses: string[]
  decisions: string[]
  min_match_score: number | null
  max_match_score: number | null
  match_tiers: number[]
  min_engagement_signals: number | null
  engagement_types: string[]
  nationalities: string[]
  has_applied: boolean | null
  applied_after: string
}

const EMPTY_CRITERIA: CriteriaState = {
  statuses: [],
  decisions: [],
  min_match_score: null,
  max_match_score: null,
  match_tiers: [],
  min_engagement_signals: null,
  engagement_types: [],
  nationalities: [],
  has_applied: null,
  applied_after: '',
}

/** Convert CriteriaState to a clean JSON object (omit null / empty). */
function criteriaStateToJson(c: CriteriaState): Record<string, unknown> {
  const out: Record<string, unknown> = {}
  if (c.statuses.length) out.statuses = c.statuses
  if (c.decisions.length) out.decisions = c.decisions
  if (c.min_match_score != null) out.min_match_score = c.min_match_score
  if (c.max_match_score != null) out.max_match_score = c.max_match_score
  if (c.match_tiers.length) out.match_tiers = c.match_tiers
  if (c.min_engagement_signals != null) out.min_engagement_signals = c.min_engagement_signals
  if (c.engagement_types.length) out.engagement_types = c.engagement_types
  if (c.nationalities.length) out.nationalities = c.nationalities
  if (c.has_applied != null) out.has_applied = c.has_applied
  if (c.applied_after) out.applied_after = c.applied_after
  return out
}

/** Parse a raw JSON object into CriteriaState (best-effort). */
function jsonToCriteriaState(obj: Record<string, unknown>): CriteriaState {
  return {
    statuses: Array.isArray(obj.statuses) ? obj.statuses : [],
    decisions: Array.isArray(obj.decisions) ? obj.decisions : [],
    min_match_score: typeof obj.min_match_score === 'number' ? obj.min_match_score : null,
    max_match_score: typeof obj.max_match_score === 'number' ? obj.max_match_score : null,
    match_tiers: Array.isArray(obj.match_tiers) ? obj.match_tiers : [],
    min_engagement_signals: typeof obj.min_engagement_signals === 'number' ? obj.min_engagement_signals : null,
    engagement_types: Array.isArray(obj.engagement_types) ? obj.engagement_types : [],
    nationalities: Array.isArray(obj.nationalities) ? obj.nationalities : [],
    has_applied: typeof obj.has_applied === 'boolean' ? obj.has_applied : null,
    applied_after: typeof obj.applied_after === 'string' ? obj.applied_after : '',
  }
}

/* ------------------------------------------------------------------ */
/*  Human-readable criteria badges                                     */
/* ------------------------------------------------------------------ */

function criteriaToBadges(criteria: Record<string, unknown> | null | undefined): string[] {
  if (!criteria || Object.keys(criteria).length === 0) return []
  const badges: string[] = []
  const c = criteria as Record<string, unknown>
  if (Array.isArray(c.statuses) && c.statuses.length)
    badges.push(`Status: ${c.statuses.join(', ')}`)
  if (Array.isArray(c.decisions) && c.decisions.length)
    badges.push(`Decision: ${c.decisions.join(', ')}`)
  if (typeof c.min_match_score === 'number' && typeof c.max_match_score === 'number')
    badges.push(`Match: ${c.min_match_score}-${c.max_match_score}`)
  else if (typeof c.min_match_score === 'number')
    badges.push(`Match: ${c.min_match_score}+`)
  else if (typeof c.max_match_score === 'number')
    badges.push(`Match: <=${c.max_match_score}`)
  if (Array.isArray(c.match_tiers) && c.match_tiers.length) {
    const tierLabels: Record<number, string> = { 1: 'Reach', 2: 'Match', 3: 'Safety' }
    badges.push(`Tier: ${(c.match_tiers as number[]).map(t => tierLabels[t] ?? t).join(', ')}`)
  }
  if (typeof c.min_engagement_signals === 'number')
    badges.push(`Engagement: >=${c.min_engagement_signals}`)
  if (Array.isArray(c.engagement_types) && c.engagement_types.length)
    badges.push(`Signal: ${c.engagement_types.join(', ')}`)
  if (Array.isArray(c.nationalities) && c.nationalities.length)
    badges.push(`Nationality: ${c.nationalities.join(', ')}`)
  if (c.has_applied === true) badges.push('Has applied')
  if (c.has_applied === false) badges.push('No application')
  if (typeof c.applied_after === 'string' && c.applied_after)
    badges.push(`Applied after: ${c.applied_after}`)
  return badges
}

/* ------------------------------------------------------------------ */
/*  Constants                                                          */
/* ------------------------------------------------------------------ */

const APPLICATION_STATUSES = ['submitted', 'under_review', 'interview', 'decision_made'] as const
const DECISION_VALUES = ['admitted', 'rejected', 'waitlisted', 'deferred'] as const
const TIER_OPTIONS = [
  { value: 1, label: 'Reach' },
  { value: 2, label: 'Match' },
  { value: 3, label: 'Safety' },
] as const

const SEGMENT_TEMPLATES = [
  { value: '', label: 'Custom segment', criteria: {} },
  { value: 'high_match', label: 'High match score (80+)', criteria: { min_match_score: 80 } },
  { value: 'under_review', label: 'Applications under review', criteria: { statuses: ['submitted', 'under_review'] } },
  { value: 'interview_ready', label: 'Interview stage candidates', criteria: { statuses: ['interview'] } },
  { value: 'admitted_yield_risk', label: 'Admitted -- yield risk', criteria: { decisions: ['admitted'], statuses: ['decision_made'] } },
  { value: 'high_engagement_no_app', label: 'High engagement, no application', criteria: { min_engagement_signals: 3, has_applied: false } },
  { value: 'recent_applicants', label: 'Applied in last 30 days', criteria: { applied_after: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0] } },
]

/* ------------------------------------------------------------------ */
/*  Checkbox group helpers                                             */
/* ------------------------------------------------------------------ */

function CheckboxGroup({ label, options, selected, onChange }: {
  label: string
  options: readonly string[]
  selected: string[]
  onChange: (next: string[]) => void
}) {
  const toggle = (v: string) => {
    onChange(selected.includes(v) ? selected.filter(s => s !== v) : [...selected, v])
  }
  return (
    <div>
      <span className="block text-sm font-medium text-gray-700 mb-1">{label}</span>
      <div className="flex flex-wrap gap-2">
        {options.map(o => (
          <label key={o} className="flex items-center gap-1 text-sm cursor-pointer select-none">
            <input type="checkbox" checked={selected.includes(o)} onChange={() => toggle(o)} className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500" />
            <span className="text-gray-700">{o.replace(/_/g, ' ')}</span>
          </label>
        ))}
      </div>
    </div>
  )
}

function NumberCheckboxGroup({ label, options, selected, onChange }: {
  label: string
  options: readonly { value: number; label: string }[]
  selected: number[]
  onChange: (next: number[]) => void
}) {
  const toggle = (v: number) => {
    onChange(selected.includes(v) ? selected.filter(s => s !== v) : [...selected, v])
  }
  return (
    <div>
      <span className="block text-sm font-medium text-gray-700 mb-1">{label}</span>
      <div className="flex flex-wrap gap-2">
        {options.map(o => (
          <label key={o.value} className="flex items-center gap-1 text-sm cursor-pointer select-none">
            <input type="checkbox" checked={selected.includes(o.value)} onChange={() => toggle(o.value)} className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500" />
            <span className="text-gray-700">{o.label}</span>
          </label>
        ))}
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  CriteriaBuilder component                                          */
/* ------------------------------------------------------------------ */

function CriteriaBuilder({ criteria, onChange }: { criteria: CriteriaState; onChange: (c: CriteriaState) => void }) {
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [rawJson, setRawJson] = useState('')

  const openAdvanced = () => {
    setRawJson(JSON.stringify(criteriaStateToJson(criteria), null, 2))
    setShowAdvanced(true)
  }

  const applyRawJson = () => {
    try {
      const parsed = JSON.parse(rawJson)
      onChange(jsonToCriteriaState(parsed))
      setShowAdvanced(false)
    } catch {
      showToast('Invalid JSON', 'error')
    }
  }

  return (
    <div className="space-y-4 border rounded-lg p-4 bg-gray-50">
      {/* Application Status */}
      <CheckboxGroup
        label="Application Status"
        options={APPLICATION_STATUSES}
        selected={criteria.statuses}
        onChange={statuses => onChange({ ...criteria, statuses })}
      />

      {/* Decision */}
      <CheckboxGroup
        label="Decision"
        options={DECISION_VALUES}
        selected={criteria.decisions}
        onChange={decisions => onChange({ ...criteria, decisions })}
      />

      {/* Match Score Range */}
      <div>
        <span className="block text-sm font-medium text-gray-700 mb-1">Match Score Range (0-100)</span>
        <div className="flex items-center gap-2">
          <input
            type="number"
            min={0}
            max={100}
            placeholder="Min"
            value={criteria.min_match_score ?? ''}
            onChange={e => onChange({ ...criteria, min_match_score: e.target.value ? Number(e.target.value) : null })}
            className="w-24 rounded-md border-gray-300 shadow-sm text-sm focus:border-indigo-500 focus:ring-indigo-500"
          />
          <span className="text-gray-400">to</span>
          <input
            type="number"
            min={0}
            max={100}
            placeholder="Max"
            value={criteria.max_match_score ?? ''}
            onChange={e => onChange({ ...criteria, max_match_score: e.target.value ? Number(e.target.value) : null })}
            className="w-24 rounded-md border-gray-300 shadow-sm text-sm focus:border-indigo-500 focus:ring-indigo-500"
          />
        </div>
      </div>

      {/* Match Tier */}
      <NumberCheckboxGroup
        label="Match Tier"
        options={TIER_OPTIONS}
        selected={criteria.match_tiers}
        onChange={match_tiers => onChange({ ...criteria, match_tiers })}
      />

      {/* Min Engagement Signals */}
      <div>
        <span className="block text-sm font-medium text-gray-700 mb-1">Min Engagement Signals</span>
        <input
          type="number"
          min={0}
          placeholder="e.g. 3"
          value={criteria.min_engagement_signals ?? ''}
          onChange={e => onChange({ ...criteria, min_engagement_signals: e.target.value ? Number(e.target.value) : null })}
          className="w-32 rounded-md border-gray-300 shadow-sm text-sm focus:border-indigo-500 focus:ring-indigo-500"
        />
      </div>

      {/* Nationality */}
      <div>
        <span className="block text-sm font-medium text-gray-700 mb-1">Nationality (comma-separated)</span>
        <input
          type="text"
          placeholder="e.g. US, CN, IN"
          value={criteria.nationalities.join(', ')}
          onChange={e => onChange({ ...criteria, nationalities: e.target.value ? e.target.value.split(',').map(s => s.trim()).filter(Boolean) : [] })}
          className="w-full rounded-md border-gray-300 shadow-sm text-sm focus:border-indigo-500 focus:ring-indigo-500"
        />
      </div>

      {/* Has Applied */}
      <div>
        <span className="block text-sm font-medium text-gray-700 mb-1">Application Requirement</span>
        <div className="flex gap-4">
          {([null, true, false] as const).map(val => (
            <label key={String(val)} className="flex items-center gap-1 text-sm cursor-pointer select-none">
              <input
                type="radio"
                name="has_applied"
                checked={criteria.has_applied === val}
                onChange={() => onChange({ ...criteria, has_applied: val })}
                className="text-indigo-600 focus:ring-indigo-500"
              />
              <span className="text-gray-700">{val === null ? 'Any' : val ? 'Has applied' : 'No application'}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Applied After */}
      <div>
        <span className="block text-sm font-medium text-gray-700 mb-1">Applied After</span>
        <input
          type="date"
          value={criteria.applied_after}
          onChange={e => onChange({ ...criteria, applied_after: e.target.value })}
          className="rounded-md border-gray-300 shadow-sm text-sm focus:border-indigo-500 focus:ring-indigo-500"
        />
      </div>

      {/* Advanced JSON toggle */}
      <div className="border-t pt-3">
        {!showAdvanced ? (
          <button onClick={openAdvanced} className="flex items-center gap-1 text-sm text-indigo-600 hover:underline">
            <ChevronDown size={14} /> Advanced (raw JSON)
          </button>
        ) : (
          <div className="space-y-2">
            <button onClick={() => setShowAdvanced(false)} className="flex items-center gap-1 text-sm text-indigo-600 hover:underline">
              <ChevronUp size={14} /> Hide JSON
            </button>
            <Textarea
              label=""
              value={rawJson}
              onChange={e => setRawJson(e.target.value)}
              rows={6}
            />
            <Button size="sm" variant="ghost" onClick={applyRawJson}>Apply JSON</Button>
          </div>
        )}
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Main page component                                                */
/* ------------------------------------------------------------------ */

export default function SegmentsPage() {
  const queryClient = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const [name, setName] = useState('')
  const [programId, setProgramId] = useState('')
  const [criteriaState, setCriteriaState] = useState<CriteriaState>({ ...EMPTY_CRITERIA })
  const [templateKey, setTemplateKey] = useState('')
  const [isActive, setIsActive] = useState(true)
  const [audienceCounts, setAudienceCounts] = useState<Record<string, number>>({})

  const loadAudienceCount = async (segId: string) => {
    try {
      const res = await previewSegmentAudience(segId)
      setAudienceCounts(prev => ({ ...prev, [segId]: res.audience_count }))
    } catch { /* ignore */ }
  }

  const segmentsQ = useQuery({ queryKey: ['segments'], queryFn: getSegments })
  const segments: Segment[] = Array.isArray(segmentsQ.data) ? segmentsQ.data : []

  const programsQ = useQuery({ queryKey: ['institution-programs'], queryFn: getInstitutionPrograms })
  const programs: Program[] = Array.isArray(programsQ.data) ? programsQ.data : []
  const programOptions = [{ value: '', label: 'None' }, ...programs.map(p => ({ value: p.id, label: p.program_name }))]

  const resetForm = useCallback(() => {
    setEditId(null)
    setName('')
    setProgramId('')
    setCriteriaState({ ...EMPTY_CRITERIA })
    setTemplateKey('')
    setIsActive(true)
  }, [])

  const openCreate = () => { resetForm(); setShowModal(true) }
  const openEdit = (seg: Segment) => {
    setEditId(seg.id)
    setName(seg.segment_name)
    setProgramId(seg.program_id ?? '')
    setCriteriaState(jsonToCriteriaState(seg.criteria ?? {}))
    setTemplateKey('')
    setIsActive(seg.is_active)
    setShowModal(true)
  }

  const createMut = useMutation({
    mutationFn: createSegment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['segments'] })
      showToast('Segment created', 'success')
      setShowModal(false)
    },
    onError: () => showToast('Failed to create segment', 'error'),
  })

  const updateMut = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: any }) => updateSegment(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['segments'] })
      showToast('Segment updated', 'success')
      setShowModal(false)
    },
    onError: () => showToast('Failed to update segment', 'error'),
  })

  const deleteMut = useMutation({
    mutationFn: deleteSegment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['segments'] })
      showToast('Segment deleted', 'success')
    },
    onError: () => showToast('Failed to delete segment', 'error'),
  })

  const handleSubmit = () => {
    if (!name.trim()) { showToast('Name is required', 'warning'); return }
    const criteria = criteriaStateToJson(criteriaState)

    const payload = {
      segment_name: name,
      program_id: programId || null,
      criteria,
      is_active: isActive,
    }

    if (editId) {
      updateMut.mutate({ id: editId, payload })
    } else {
      createMut.mutate(payload)
    }
  }

  return (
    <div className="p-6 space-y-4">
      <InstitutionPageHeader
        title="Recruitment Segments"
        description="Group applicants by shared traits to run targeted outreach."
        actions={(
          <Button onClick={openCreate} className="flex items-center gap-2">
            <Plus size={16} /> New Segment
          </Button>
        )}
      />

      {segmentsQ.isLoading ? (
        <div className="grid grid-cols-2 gap-4">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-32" />)}</div>
      ) : segments.length === 0 ? (
        <EmptyState
          icon={<Layers size={40} />}
          title="No segments"
          description="Create segments to target specific student populations."
          action={{ label: 'New Segment', onClick: openCreate }}
        />
      ) : (
        <div className="grid grid-cols-2 gap-4">
          {segments.map(seg => {
            const prog = programs.find(p => p.id === seg.program_id)
            const badges = criteriaToBadges(seg.criteria)
            return (
              <Card key={seg.id} className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h3 className="font-semibold text-gray-900">{seg.segment_name}</h3>
                    {prog && <p className="text-xs text-gray-500">{prog.program_name}</p>}
                  </div>
                  <Badge variant={seg.is_active ? 'success' : 'neutral'}>
                    {seg.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                </div>
                <p className="text-xs text-gray-400 mb-2">Created {formatDate(seg.created_at)}</p>
                <div className="flex items-center gap-2 mb-3 text-sm">
                  <span className="text-gray-500">Audience:</span>
                  {audienceCounts[seg.id] != null ? (
                    <span className="font-semibold text-gray-900">{audienceCounts[seg.id]} students</span>
                  ) : (
                    <button onClick={() => loadAudienceCount(seg.id)} className="text-indigo-600 hover:underline text-xs">
                      Preview
                    </button>
                  )}
                </div>
                <div className="flex flex-wrap gap-1 mb-3">
                  {badges.length === 0 ? (
                    <Badge variant="neutral">All applicants</Badge>
                  ) : (
                    <>
                      {badges.slice(0, 4).map((b, i) => (
                        <Badge key={i} variant="info">{b}</Badge>
                      ))}
                      {badges.length > 4 && (
                        <Badge variant="neutral">+{badges.length - 4} more</Badge>
                      )}
                    </>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button variant="ghost" size="sm" onClick={() => openEdit(seg)} className="flex items-center gap-1">
                    <Edit2 size={14} /> Edit
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => deleteMut.mutate(seg.id)} className="flex items-center gap-1 text-red-600">
                    <Trash2 size={14} /> Delete
                  </Button>
                </div>
              </Card>
            )
          })}
        </div>
      )}

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title={editId ? 'Edit Segment' : 'New Segment'}>
        <div className="space-y-4">
          <Input label="Segment Name *" value={name} onChange={e => setName(e.target.value)} />
          <Select label="Program" options={programOptions} value={programId} onChange={e => setProgramId(e.target.value)} />
          <Select
            label="Template"
            options={SEGMENT_TEMPLATES.map(t => ({ value: t.value, label: t.label }))}
            value={templateKey}
            onChange={e => {
              const next = e.target.value
              setTemplateKey(next)
              const template = SEGMENT_TEMPLATES.find(t => t.value === next)
              if (template) setCriteriaState(jsonToCriteriaState(template.criteria))
            }}
          />
          <CriteriaBuilder criteria={criteriaState} onChange={setCriteriaState} />
          <div className="flex items-center gap-2">
            <button onClick={() => setIsActive(!isActive)} className="text-gray-600">
              {isActive ? <ToggleRight size={24} className="text-green-500" /> : <ToggleLeft size={24} className="text-gray-400" />}
            </button>
            <span className="text-sm text-gray-700">{isActive ? 'Active' : 'Inactive'}</span>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setShowModal(false)}>Cancel</Button>
            <Button onClick={handleSubmit} disabled={createMut.isPending || updateMut.isPending}>
              {(createMut.isPending || updateMut.isPending) ? 'Saving...' : 'Save'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
