import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Layers, Plus, Edit2, Trash2, ArrowRight, ArrowLeft, Code2 } from 'lucide-react'
import {
  getSegments,
  createSegment,
  updateSegment,
  deleteSegment,
  getInstitutionPrograms,
  getSegmentSignalDictionary,
  previewSegmentRules,
} from '../../api/institutions'
import InstitutionPageHeader from '../../components/institution/InstitutionPageHeader'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import Select from '../../components/ui/Select'
import Textarea from '../../components/ui/Textarea'
import EmptyState from '../../components/ui/EmptyState'
import Skeleton from '../../components/ui/Skeleton'
import QueryError from '../../components/ui/QueryError'
import { showToast } from '../../stores/toast-store'
import { confirmDialog } from '../../stores/confirm-store'
import type { NLBridgeResult, Program, Segment, SegmentPreview, SegmentRuleTree } from '../../types'
import RuleBranch from './segments/RuleBranch'
import RuleChip from './segments/RuleChip'
import AudiencePreview from './segments/AudiencePreview'
import NLAssistBar from './segments/NLAssistBar'
import {
  emptyTree,
  indexSignals,
  normalizeStoredRules,
  rulesToTree,
  treeHasRules,
} from './segments/helpers'

export default function SegmentsPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [mode, setMode] = useState<'list' | 'edit'>('list')

  const segmentsQ = useQuery({ queryKey: ['segments'], queryFn: getSegments })
  const programsQ = useQuery({
    queryKey: ['institution-programs'],
    queryFn: getInstitutionPrograms,
  })
  const dictQ = useQuery({
    queryKey: ['segment-signal-dictionary'],
    queryFn: getSegmentSignalDictionary,
  })

  const segments: Segment[] = Array.isArray(segmentsQ.data) ? segmentsQ.data : []
  const programs: Program[] = Array.isArray(programsQ.data) ? programsQ.data : []
  const signals = useMemo(() => indexSignals(dictQ.data), [dictQ.data])

  // ── builder state ──
  const [editId, setEditId] = useState<string | null>(null)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [programId, setProgramId] = useState('')
  const [tree, setTree] = useState<SegmentRuleTree>(emptyTree())
  const [freqCap, setFreqCap] = useState<string>('')
  const [isActive, setIsActive] = useState(true)
  const [showRaw, setShowRaw] = useState(false)
  const [rawText, setRawText] = useState('')
  const [preview, setPreview] = useState<SegmentPreview | undefined>()
  const [previewRan, setPreviewRan] = useState(false)

  const programOptions = [
    { value: '', label: 'All programs' },
    ...programs.map((p) => ({ value: p.id, label: p.program_name })),
  ]

  const resetBuilder = () => {
    setEditId(null)
    setName('')
    setDescription('')
    setProgramId('')
    setTree(emptyTree())
    setFreqCap('')
    setIsActive(true)
    setShowRaw(false)
    setPreview(undefined)
    setPreviewRan(false)
  }

  const openCreate = () => {
    resetBuilder()
    setMode('edit')
  }

  const openEdit = (seg: Segment) => {
    setEditId(seg.id)
    setName(seg.segment_name)
    setDescription(seg.description ?? '')
    setProgramId(seg.program_id ?? '')
    setTree(normalizeStoredRules(seg.rules))
    setFreqCap(seg.frequency_cap_per_week != null ? String(seg.frequency_cap_per_week) : '')
    setIsActive(seg.is_active)
    setShowRaw(false)
    setPreview(undefined)
    setPreviewRan(false)
    setMode('edit')
  }

  const previewMut = useMutation({
    mutationFn: () => previewSegmentRules({ rules: tree, program_id: programId || null }),
    onSuccess: (res) => {
      setPreview(res)
      setPreviewRan(true)
    },
    onError: () => showToast('Could not preview audience', 'error'),
  })

  const saveMut = useMutation({
    mutationFn: () => {
      const payload = {
        segment_name: name.trim(),
        description: description.trim() || null,
        program_id: programId || null,
        rules: tree,
        frequency_cap_per_week: freqCap ? Number(freqCap) : null,
        is_active: isActive,
      }
      return editId ? updateSegment(editId, payload) : createSegment(payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['segments'] })
      showToast(editId ? 'Segment updated' : 'Segment created', 'success')
      setMode('list')
      resetBuilder()
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

  const handleDelete = async (seg: Segment) => {
    const ok = await confirmDialog({
      title: 'Delete segment?',
      body: `“${seg.segment_name}” will be removed. Campaigns and events using it will lose this audience.`,
      confirmLabel: 'Delete',
      destructive: true,
    })
    if (!ok) return
    deleteMut.mutate(seg.id)
  }

  const applyNl = (res: NLBridgeResult) => {
    const incoming = rulesToTree(res.rules)
    // merge into the current tree (append, don't clobber existing rules)
    setTree((prev) => ({
      include: { ...prev.include, rules: [...prev.include.rules, ...incoming.include.rules] },
      exclude: { ...prev.exclude, rules: [...prev.exclude.rules, ...incoming.exclude.rules] },
    }))
    setPreviewRan(false)
  }

  const handleSave = () => {
    if (!name.trim()) {
      showToast('Give the segment a name', 'warning')
      return
    }
    saveMut.mutate()
  }

  const goToCampaign = (segId: string) => {
    navigate(`/i/outreach?tab=campaigns&segment=${segId}`)
  }

  const applyRaw = () => {
    try {
      const parsed = JSON.parse(rawText)
      setTree(normalizeStoredRules(parsed))
      setShowRaw(false)
      setPreviewRan(false)
      showToast('Applied raw rules', 'success')
    } catch {
      showToast('Invalid JSON', 'error')
    }
  }

  // ════════════════════════ LIST VIEW ════════════════════════
  if (mode === 'list') {
    return (
      <div className="space-y-4 p-6">
        <InstitutionPageHeader
          title="Audience Segments"
          description="Build reusable audiences for campaigns, events, and follow-ups — no SQL required."
          actions={
            <Button variant="secondary" onClick={openCreate} className="flex items-center gap-2">
              <Plus size={16} /> New segment
            </Button>
          }
        />

        {dictQ.isError && (
          <p className="text-xs text-muted-foreground">
            We couldn't load the signal dictionary, so rule labels may be incomplete.{' '}
            <button onClick={() => dictQ.refetch()} className="font-medium text-secondary hover:underline">
              Try again
            </button>
          </p>
        )}

        {segmentsQ.isLoading ? (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-40" />
            ))}
          </div>
        ) : segmentsQ.isError ? (
          <QueryError detail="We couldn't load your segments." onRetry={() => segmentsQ.refetch()} />
        ) : segments.length === 0 ? (
          <EmptyState
            icon={<Layers size={40} />}
            title="No segments yet"
            description="Build one to target campaigns and events."
            action={{ label: 'New segment', onClick: openCreate }}
          />
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {segments.map((seg) => (
              <SegmentCard
                key={seg.id}
                seg={seg}
                programName={programs.find((p) => p.id === seg.program_id)?.program_name}
                signals={signals}
                onEdit={() => openEdit(seg)}
                onDelete={() => handleDelete(seg)}
                onUseInCampaign={() => goToCampaign(seg.id)}
              />
            ))}
          </div>
        )}
      </div>
    )
  }

  // ════════════════════════ BUILDER VIEW ════════════════════════
  return (
    <div className="space-y-4 p-6">
      <button
        type="button"
        onClick={() => {
          setMode('list')
          resetBuilder()
        }}
        className="flex items-center gap-1 text-sm text-secondary hover:underline"
      >
        <ArrowLeft size={15} /> Back to segments
      </button>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left: editor */}
        <div className="space-y-5 lg:col-span-2">
          <Card className="space-y-4 p-5">
            <Input
              label="Segment name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="High-interest CS prospects who haven't started an app"
            />
            <Textarea
              label="Description (optional)"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
            />
            <Select
              label="Program scope"
              options={programOptions}
              value={programId}
              onChange={(e) => {
                setProgramId(e.target.value)
                setPreviewRan(false)
              }}
            />
          </Card>

          <NLAssistBar onApply={applyNl} />

          <Card className="space-y-4 p-5">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-foreground">Rules</h3>
              <button
                type="button"
                onClick={() => {
                  setRawText(JSON.stringify(tree, null, 2))
                  setShowRaw((v) => !v)
                }}
                className="flex items-center gap-1 text-xs text-muted-foreground hover:text-secondary"
              >
                <Code2 size={13} /> {showRaw ? 'Hide' : 'Raw rule editor'}
              </button>
            </div>

            {showRaw ? (
              <div className="space-y-2">
                <Textarea
                  label=""
                  value={rawText}
                  onChange={(e) => setRawText(e.target.value)}
                  rows={12}
                />
                <Button variant="tertiary" size="sm" onClick={applyRaw}>
                  Apply JSON
                </Button>
              </div>
            ) : (
              <div className="space-y-3" onClickCapture={() => setPreviewRan(false)}>
                <RuleBranch
                  title="Include"
                  hint="Students must match these to enter the audience."
                  branch="include"
                  group={tree.include}
                  signals={signals}
                  dict={dictQ.data}
                  onChange={(g) => setTree((t) => ({ ...t, include: g }))}
                />
                <RuleBranch
                  title="Exclude"
                  hint="Students matching any of these are removed."
                  branch="exclude"
                  group={tree.exclude}
                  signals={signals}
                  dict={dictQ.data}
                  onChange={(g) => setTree((t) => ({ ...t, exclude: g }))}
                />
              </div>
            )}
          </Card>

          <Card className="flex flex-wrap items-center gap-4 p-5">
            <div className="flex items-center gap-2">
              <label className="text-sm text-muted-foreground" htmlFor="freq-cap">
                Max sends / week
              </label>
              <input
                id="freq-cap"
                type="number"
                min={0}
                value={freqCap}
                onChange={(e) => setFreqCap(e.target.value)}
                placeholder="∞"
                className="w-20 rounded-md border-border text-sm focus:border-secondary focus:ring-secondary"
              />
            </div>
            <label className="flex cursor-pointer items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
                className="rounded border-border text-secondary focus:ring-secondary"
              />
              <span className="text-foreground">Active</span>
            </label>
            <p className="text-xs text-muted-foreground">
              Students who opted out of outreach are always suppressed automatically.
            </p>
          </Card>
        </div>

        {/* Right: preview + actions */}
        <div className="space-y-4">
          <div className="sticky top-4 space-y-4">
            <AudiencePreview preview={preview} loading={previewMut.isPending} hasRun={previewRan} />
            <div className="flex flex-col gap-2">
              <Button
                variant="tertiary"
                onClick={() => previewMut.mutate()}
                disabled={!treeHasRules(tree) && !programId}
              >
                Preview audience
              </Button>
              <Button variant="secondary" onClick={handleSave} loading={saveMut.isPending}>
                {editId ? 'Save changes' : 'Save segment'}
              </Button>
              {editId && (
                <Button
                  variant="ghost"
                  onClick={() => goToCampaign(editId)}
                  className="flex items-center justify-center gap-1 text-secondary"
                >
                  Use in campaign <ArrowRight size={15} />
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ── Segment card (list view) ────────────────────────────────────────────── */

function SegmentCard({
  seg,
  programName,
  signals,
  onEdit,
  onDelete,
  onUseInCampaign,
}: {
  seg: Segment
  programName?: string
  signals: Record<string, import('../../types').SignalDef>
  onEdit: () => void
  onDelete: () => void
  onUseInCampaign: () => void
}) {
  const tree = normalizeStoredRules(seg.rules)
  const allRules = [...tree.include.rules, ...tree.exclude.rules].filter(
    (r): r is import('../../types').SegmentRule => 'field' in r,
  )
  const isLegacy = !seg.rules && seg.criteria && Object.keys(seg.criteria).length > 0

  return (
    <Card className="flex flex-col p-4">
      <div className="mb-1 flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-foreground">{seg.segment_name}</h3>
          {programName && <p className="text-xs text-muted-foreground">{programName}</p>}
        </div>
        <Badge variant={seg.is_active ? 'success' : 'neutral'}>
          {seg.is_active ? 'Active' : 'Inactive'}
        </Badge>
      </div>
      {seg.description && <p className="mb-2 text-sm text-muted-foreground">{seg.description}</p>}

      {/* Audience count — cached preview, in --accent */}
      <div className="mb-3 text-sm">
        {seg.preview_audience_count != null ? (
          <span className="font-semibold text-secondary">
            ~{seg.preview_audience_count.toLocaleString()} students
          </span>
        ) : (
          <span className="text-muted-foreground">Open to preview audience</span>
        )}
      </div>

      <div className="mb-3 flex flex-1 flex-wrap gap-1.5">
        {isLegacy ? (
          <Badge variant="neutral">Legacy criteria</Badge>
        ) : allRules.length === 0 ? (
          <Badge variant="neutral">All connected students</Badge>
        ) : (
          allRules
            .slice(0, 5)
            .map((rule, i) => <RuleChip key={i} signal={signals[rule.field]} rule={rule} />)
        )}
        {allRules.length > 5 && <Badge variant="neutral">+{allRules.length - 5} more</Badge>}
      </div>

      <div className="flex items-center gap-2 border-t border-border pt-3">
        <Button variant="ghost" size="sm" onClick={onEdit} className="flex items-center gap-1">
          <Edit2 size={14} /> Edit
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={onUseInCampaign}
          className="flex items-center gap-1 text-secondary"
        >
          Use in campaign <ArrowRight size={14} />
        </Button>
        <button
          type="button"
          onClick={onDelete}
          aria-label="Delete segment"
          className="ml-auto rounded-md p-1.5 text-muted-foreground hover:bg-error-soft hover:text-error"
        >
          <Trash2 size={14} />
        </button>
      </div>
    </Card>
  )
}
