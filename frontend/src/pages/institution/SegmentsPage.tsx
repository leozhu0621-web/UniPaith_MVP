import { useCallback, useMemo, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Layers, Plus, Edit2, Trash2, ToggleLeft, ToggleRight, Sparkles, Loader2, ArrowRight } from 'lucide-react'
import {
  getSegments,
  createSegment,
  updateSegment,
  deleteSegment,
  getInstitutionPrograms,
  previewSegmentAudience,
  previewSegmentAudienceDraft,
  segmentNlBridge,
  getDatasets,
} from '../../api/institutions'
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
import ConstraintChip from '../../components/ui/ConstraintChip'
import SegmentRuleEditor from './segments/SegmentRuleEditor'
import {
  criteriaToPayload,
  payloadToCriteria,
  flattenRules,
  plainLanguageRule,
  defaultIncludeTree,
  defaultExcludeTree,
  type SegmentCriteriaPayload,
  type SegmentRule,
} from './segments/segmentRules'
import { showToast } from '../../stores/toast-store'
import { formatDate } from '../../utils/format'
import type { InstitutionDataset, Segment, Program, SegmentAudiencePreview, SegmentNlBridgeResult } from '../../types'

type ActiveFilter = 'all' | 'active' | 'inactive'

const EMPTY_CRITERIA: SegmentCriteriaPayload = {
  description: '',
  frequency_cap_per_week: null,
  uploaded_list_ids: [],
  include: defaultIncludeTree(),
  exclude: defaultExcludeTree(),
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

function allRulesFromCriteria(criteria: Record<string, unknown> | null | undefined): SegmentRule[] {
  const parsed = payloadToCriteria(criteria ?? {})
  return [...flattenRules(parsed.include), ...flattenRules(parsed.exclude)]
}

export default function SegmentsPage() {
  const queryClient = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const [name, setName] = useState('')
  const [programId, setProgramId] = useState('')
  const [criteria, setCriteria] = useState<SegmentCriteriaPayload>({ ...EMPTY_CRITERIA })
  const [isActive, setIsActive] = useState(true)
  const [activeFilter, setActiveFilter] = useState<ActiveFilter>('active')
  const [audienceCounts, setAudienceCounts] = useState<Record<string, number>>({})
  const [previewLoading, setPreviewLoading] = useState(false)
  const [draftPreview, setDraftPreview] = useState<SegmentAudiencePreview | null>(null)
  const [nlInput, setNlInput] = useState('')
  const [nlLoading, setNlLoading] = useState(false)
  const [nlResult, setNlResult] = useState<SegmentNlBridgeResult | null>(null)
  const [rawJson, setRawJson] = useState('')

  const segmentsQ = useQuery({ queryKey: ['segments'], queryFn: getSegments })
  const segments: Segment[] = Array.isArray(segmentsQ.data) ? segmentsQ.data : []

  const programsQ = useQuery({ queryKey: ['institution-programs'], queryFn: getInstitutionPrograms })
  const programs: Program[] = Array.isArray(programsQ.data) ? programsQ.data : []
  const programOptions = [{ value: '', label: 'All programs' }, ...programs.map(p => ({ value: p.id, label: p.program_name }))]

  const datasetsQ = useQuery({ queryKey: ['institution-datasets'], queryFn: getDatasets })
  const prospectLists: InstitutionDataset[] = (Array.isArray(datasetsQ.data) ? datasetsQ.data : []).filter(
    d => d.dataset_type === 'prospect_list' && (d.status === 'processed' || d.status === 'active')
  )

  const filteredSegments = useMemo(() => {
    if (activeFilter === 'all') return segments
    if (activeFilter === 'active') return segments.filter(s => s.is_active)
    return segments.filter(s => !s.is_active)
  }, [segments, activeFilter])

  const resetForm = useCallback(() => {
    setEditId(null)
    setName('')
    setProgramId('')
    setCriteria({ ...EMPTY_CRITERIA, include: defaultIncludeTree(), exclude: defaultExcludeTree() })
    setIsActive(true)
    setDraftPreview(null)
    setNlInput('')
    setNlResult(null)
    setRawJson('')
  }, [])

  const openCreate = () => { resetForm(); setShowModal(true) }

  const openEdit = (seg: Segment) => {
    const parsed = payloadToCriteria(seg.criteria ?? {})
    setEditId(seg.id)
    setName(seg.segment_name)
    setProgramId(seg.program_id ?? '')
    setCriteria(parsed)
    setIsActive(seg.is_active)
    setDraftPreview(null)
    setNlInput('')
    setNlResult(null)
    setRawJson(JSON.stringify(criteriaToPayload(parsed), null, 2))
    setShowModal(true)
  }

  const createMut = useMutation({
    mutationFn: createSegment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['segments'] })
      showToast('Segment saved', 'success')
      setShowModal(false)
    },
    onError: () => showToast('Failed to save segment', 'error'),
  })

  const updateMut = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Record<string, unknown> }) => updateSegment(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['segments'] })
      showToast('Segment saved', 'success')
      setShowModal(false)
    },
    onError: () => showToast('Failed to save segment', 'error'),
  })

  const deleteMut = useMutation({
    mutationFn: deleteSegment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['segments'] })
      showToast('Segment deleted', 'success')
    },
    onError: () => showToast('Failed to delete segment', 'error'),
  })

  const loadAudienceCount = async (segId: string) => {
    try {
      const res = await previewSegmentAudience(segId)
      setAudienceCounts(prev => ({ ...prev, [segId]: res.audience_count }))
    } catch {
      showToast('Could not preview audience', 'error')
    }
  }

  const runDraftPreview = async () => {
    setPreviewLoading(true)
    setDraftPreview(null)
    try {
      const payload = { program_id: programId || null, criteria: criteriaToPayload(criteria) }
      const res = editId ? await previewSegmentAudience(editId) : await previewSegmentAudienceDraft(payload)
      setDraftPreview(res)
    } catch {
      showToast('Could not preview audience', 'error')
    } finally {
      setPreviewLoading(false)
    }
  }

  const runNlBridge = async () => {
    if (!nlInput.trim()) return
    setNlLoading(true)
    setNlResult(null)
    try {
      const res = await segmentNlBridge(nlInput.trim())
      setNlResult(res)
      const includeRules: SegmentRule[] = res.rules.map(r => ({
        field: r.field,
        operator: r.operator as SegmentRule['operator'],
        value: r.value,
        ambiguous: res.ambiguity_notes.some(n => n.toLowerCase().includes(r.field)),
      }))
      setCriteria(prev => ({
        ...prev,
        include: { op: 'AND', rules: [...flattenRules(prev.include), ...includeRules] },
      }))
      showToast('Rules added — review before saving', 'success')
    } catch {
      showToast('AI assist unavailable — try adjusting your description', 'error')
    } finally {
      setNlLoading(false)
    }
  }

  const applyRawJson = () => {
    try {
      setCriteria(payloadToCriteria(JSON.parse(rawJson) as Record<string, unknown>))
      showToast('Rules applied from JSON', 'success')
    } catch {
      showToast('Invalid JSON', 'error')
    }
  }

  const handleSubmit = () => {
    if (!name.trim()) { showToast('Name is required', 'warning'); return }
    const payload = {
      segment_name: name.trim(),
      program_id: programId || null,
      criteria: criteriaToPayload(criteria),
      is_active: isActive,
    }
    if (editId) updateMut.mutate({ id: editId, payload })
    else createMut.mutate(payload)
  }

  const filterOptions = [
    { value: 'active', label: 'Active' },
    { value: 'inactive', label: 'Inactive' },
    { value: 'all', label: 'All' },
  ]

  const previewCount = draftPreview?.audience_count
  const showZeroMatch = previewCount === 0

  return (
    <div className="p-6 space-y-4">
      <InstitutionPageHeader
        title="Segments"
        description="Build reusable audiences for campaigns, event invites, and follow-ups."
        actions={(
          <Button variant="secondary" onClick={openCreate} className="flex items-center gap-2">
            <Plus size={16} /> New segment
          </Button>
        )}
      />

      <Select label="" options={filterOptions} value={activeFilter} onChange={e => setActiveFilter(e.target.value as ActiveFilter)} className="w-40" />

      {segmentsQ.isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-36" />)}
        </div>
      ) : filteredSegments.length === 0 ? (
        <EmptyState
          icon={<Layers size={40} />}
          title="No segments yet"
          description="Build one to target campaigns and events."
          action={{ label: 'New segment', onClick: openCreate }}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredSegments.map(seg => {
            const prog = programs.find(p => p.id === seg.program_id)
            const rules = allRulesFromCriteria(seg.criteria)
            return (
              <Card key={seg.id} className="p-4 flex flex-col gap-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="font-semibold text-foreground">{seg.segment_name}</h3>
                    {prog && <p className="text-xs text-muted-foreground">{prog.program_name}</p>}
                  </div>
                  <Badge variant={seg.is_active ? 'success' : 'neutral'}>{seg.is_active ? 'Active' : 'Inactive'}</Badge>
                </div>
                <p className="text-xs text-muted-foreground">Updated {formatDate(seg.updated_at ?? seg.created_at)}</p>
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-muted-foreground">Audience:</span>
                  {audienceCounts[seg.id] != null ? (
                    <span className="font-semibold text-accent">~{audienceCounts[seg.id]} students</span>
                  ) : (
                    <button type="button" onClick={() => loadAudienceCount(seg.id)} className="text-secondary text-xs hover:underline">Preview audience</button>
                  )}
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {rules.length === 0 ? (
                    <Badge variant="neutral">All prospects</Badge>
                  ) : (
                    rules.slice(0, 4).map((rule, i) => (
                      <ConstraintChip key={i} category="Rule" value={plainLanguageRule(rule)} />
                    ))
                  )}
                  {rules.length > 4 && <Badge variant="neutral">+{rules.length - 4} more</Badge>}
                </div>
                <div className="flex flex-wrap gap-2 mt-auto pt-2 border-t border-border">
                  <Button variant="ghost" size="sm" onClick={() => openEdit(seg)} className="flex items-center gap-1"><Edit2 size={14} /> Edit</Button>
                  <Button variant="ghost" size="sm" onClick={() => deleteMut.mutate(seg.id)} className="flex items-center gap-1 text-destructive"><Trash2 size={14} /> Delete</Button>
                  <Link to={`/i/campaigns?segmentId=${seg.id}`} className="ml-auto">
                    <Button variant="secondary" size="sm" className="flex items-center gap-1">Use in campaign <ArrowRight size={14} /></Button>
                  </Link>
                </div>
              </Card>
            )
          })}
        </div>
      )}

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title={editId ? 'Edit segment' : 'New segment'}>
        <div className="space-y-4 max-h-[75vh] overflow-y-auto pr-1">
          <Input label="Segment name *" value={name} onChange={e => setName(e.target.value)} placeholder="High-interest CS prospects who have not started an app" />
          <Textarea label="Description" value={criteria.description ?? ''} onChange={e => setCriteria(prev => ({ ...prev, description: e.target.value }))} rows={2} />
          <Select label="Program scope" options={programOptions} value={programId} onChange={e => setProgramId(e.target.value)} />

          {prospectLists.length > 0 && (
            <div>
              <span className="block text-sm font-medium text-foreground mb-1">Uploaded prospect lists</span>
              <div className="flex flex-wrap gap-2">
                {prospectLists.map(list => {
                  const selected = criteria.uploaded_list_ids?.includes(list.id)
                  return (
                    <button
                      key={list.id}
                      type="button"
                      onClick={() => setCriteria(prev => {
                        const ids = prev.uploaded_list_ids ?? []
                        return { ...prev, uploaded_list_ids: selected ? ids.filter(id => id !== list.id) : [...ids, list.id] }
                      })}
                      className={`text-xs px-3 py-1 rounded-pill border ${selected ? 'border-secondary bg-secondary/10 text-secondary' : 'border-border text-muted-foreground'}`}
                    >
                      {list.dataset_name}
                    </button>
                  )
                })}
              </div>
            </div>
          )}

          <div className="rounded-lg border border-border p-3 bg-card space-y-2">
            <p className="text-sm font-medium text-foreground flex items-center gap-2">
              <Sparkles size={16} className="text-accent" /> Try AI assist: type what audience you want →
            </p>
            <div className="flex gap-2">
              <Input label="" value={nlInput} onChange={e => setNlInput(e.target.value)} placeholder="students who saved Engineering programs in California with budget ≤ $40k" />
              <Button variant="secondary" onClick={runNlBridge} disabled={nlLoading || !nlInput.trim()} loading={nlLoading}>Generate</Button>
            </div>
            {nlResult && (
              <p className="text-xs text-muted-foreground">
                Confidence {nlResult.confidence_overall}%
                {nlResult.ambiguity_notes.length > 0 && ` · ${nlResult.ambiguity_notes.join('; ')}`}
              </p>
            )}
          </div>

          <SegmentRuleEditor
            include={criteria.include ?? defaultIncludeTree()}
            exclude={criteria.exclude ?? defaultExcludeTree()}
            onIncludeChange={include => setCriteria(prev => ({ ...prev, include }))}
            onExcludeChange={exclude => setCriteria(prev => ({ ...prev, exclude }))}
            rawJson={rawJson}
            onRawJsonChange={setRawJson}
            onApplyRawJson={applyRawJson}
          />

          <Input
            label="Max sends per week (optional)"
            type="number"
            min={0}
            value={criteria.frequency_cap_per_week ?? ''}
            onChange={e => setCriteria(prev => ({ ...prev, frequency_cap_per_week: e.target.value ? Number(e.target.value) : null }))}
          />

          <div className="rounded-lg border border-border p-4 bg-muted/20 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-foreground">Audience preview</span>
              <Button variant="tertiary" size="sm" onClick={runDraftPreview} disabled={previewLoading}>Preview audience</Button>
            </div>
            {previewLoading && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 size={16} className="animate-spin text-accent" /> Calculating…
              </div>
            )}
            {!previewLoading && previewCount != null && (
              <>
                <p className={`text-lg font-semibold ${showZeroMatch ? 'text-muted-foreground' : 'text-accent'}`}>
                  {showZeroMatch ? '0 students match these rules. Try widening criteria.' : `~${previewCount} students`}
                </p>
                {draftPreview?.preview_audience_sample && draftPreview.preview_audience_sample.length > 0 && (
                  <ul className="text-sm space-y-1 border-t border-border pt-2">
                    {draftPreview.preview_audience_sample.map(row => (
                      <li key={row.id} className="flex justify-between text-muted-foreground">
                        <span>{row.display_name || 'Student'}</span>
                        {row.nationality && <span className="text-xs">{row.nationality}</span>}
                      </li>
                    ))}
                  </ul>
                )}
              </>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button type="button" onClick={() => setIsActive(!isActive)} className="text-muted-foreground" aria-label="Toggle active">
              {isActive ? <ToggleRight size={24} className="text-success" /> : <ToggleLeft size={24} />}
            </button>
            <span className="text-sm text-foreground">{isActive ? 'Active' : 'Inactive'}</span>
          </div>

          <div className="flex justify-end gap-2 sticky bottom-0 bg-card pt-2">
            <Button variant="tertiary" onClick={() => setShowModal(false)}>Cancel</Button>
            <Button variant="secondary" onClick={handleSubmit} disabled={createMut.isPending || updateMut.isPending} loading={createMut.isPending || updateMut.isPending}>Save segment</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
