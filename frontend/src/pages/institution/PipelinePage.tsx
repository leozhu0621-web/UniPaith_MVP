import { useState, useMemo, useEffect, type ReactNode } from 'react'
import QueryError from '../../components/ui/QueryError'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { applicantUrl, admissionsUrl, type PipelineView } from '../../utils/institution-routes'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  useDroppable,
  useDraggable,
  type DragStartEvent,
  type DragEndEvent,
} from '@dnd-kit/core'
import { Search, GripVertical, ClipboardCheck, List, CheckSquare, Zap, Clock, Plus, Trash2 } from 'lucide-react'
import { getInstitutionPrograms } from '../../api/institutions'
import { getApplicationsByProgram, updateApplicationStatus, batchRequestMissingItems, batchUpdateStatus } from '../../api/applications-admin'
import BatchReleaseModal from './pipeline/BatchReleaseModal'
import { batchAssignReviewers, getReviewPriorityQueue } from '../../api/reviews'
import { batchInviteInterviews } from '../../api/interviews-admin'
import { showToast } from '../../stores/toast-store'
import Badge from '../../components/ui/Badge'
import Select from '../../components/ui/Select'
import Input from '../../components/ui/Input'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import Table from '../../components/ui/Table'
import Tabs from '../../components/ui/Tabs'
import Skeleton from '../../components/ui/Skeleton'
import EmptyState from '../../components/ui/EmptyState'
import { formatRelative, formatScore } from '../../utils/format'
import { STATUS_COLORS } from '../../utils/constants'
import Modal from '../../components/ui/Modal'
import Textarea from '../../components/ui/Textarea'
import type { Application, BatchOperationResult, PrioritizedApplication, Program } from '../../types'

const PIPELINE_COLUMNS = [
  { id: 'submitted', label: 'Applied', color: 'bg-secondary' },
  { id: 'under_review', label: 'Under Review', color: 'bg-warning' },
  { id: 'interview', label: 'Interview', color: 'bg-secondary' },
  { id: 'decision_made', label: 'Decision', color: 'bg-success' },
] as const

const applicantLabel = (a: { student_name?: string | null; student_id: string }) =>
  a.student_name ?? `Applicant ${a.student_id.slice(0, 8)}`

type ColumnId = typeof PIPELINE_COLUMNS[number]['id']
const PIPELINE_VIEWS: { id: PipelineView; label: string }[] = [
  { id: 'board', label: 'Board' },
  { id: 'list', label: 'List' },
  { id: 'review', label: 'Needs Review' },
  { id: 'priority', label: 'Priority' },
]

function DraggableCard({ app, onClick, selected, onToggleSelect, onGenerateOffer }: {
  app: Application; onClick: () => void; selected?: boolean; onToggleSelect?: (id: string) => void
  onGenerateOffer?: () => void
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({ id: app.id })
  const style = transform ? { transform: `translate(${transform.x}px, ${transform.y}px)` } : undefined

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`bg-card border rounded-lg p-3 cursor-pointer hover:shadow-md transition-shadow ${isDragging ? 'opacity-50' : ''} ${selected ? 'ring-2 ring-secondary border-secondary' : ''}`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-2 min-w-0 flex-1">
          {onToggleSelect && (
            <input
              type="checkbox"
              checked={selected}
              onChange={(e) => { e.stopPropagation(); onToggleSelect(app.id) }}
              onClick={(e) => e.stopPropagation()}
              className="mt-1 rounded border-border"
            />
          )}
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-foreground truncate">{applicantLabel(app)}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{app.program?.program_name ?? 'Program'}</p>
          </div>
        </div>
        <div {...listeners} {...attributes} className="p-1 cursor-grab text-muted-foreground/70">
          <GripVertical size={14} />
        </div>
      </div>
      <div className="flex items-center justify-between mt-2">
        {app.match_score != null && (
          <span className="text-xs font-medium text-secondary">{formatScore(app.match_score)}</span>
        )}
        <span className="text-xs text-muted-foreground/70">{formatRelative(app.updated_at)}</span>
      </div>
      {app.decision && (
        <Badge variant={(STATUS_COLORS[app.decision] as any) ?? 'neutral'} className="mt-1.5">
          {app.decision}
        </Badge>
      )}
      {app.status === 'decision_made' && !app.decision && onGenerateOffer && (
        <Button
          size="sm"
          variant="ghost"
          className="mt-2 h-7 w-full text-xs"
          onClick={(e) => { e.stopPropagation(); onGenerateOffer() }}
        >
          Generate offer
        </Button>
      )}
    </div>
  )
}

function DroppableColumn({ id, label, color, children }: { id: string; label: string; color: string; children: ReactNode }) {
  const { setNodeRef, isOver } = useDroppable({ id })
  return (
    <div
      ref={setNodeRef}
      className={`flex-1 min-w-[240px] rounded-lg p-3 transition-colors ${isOver ? 'bg-accent/5 ring-2 ring-accent border border-accent' : 'bg-muted'}`}
    >
      <div className="flex items-center gap-2 mb-3">
        <div className={`w-3 h-3 rounded-full ${color}`} />
        {/* Spec 31 §10 — Kanban column headers use the eyebrow style. */}
        <h3 className="text-eyebrow uppercase text-muted-foreground">{label}</h3>
      </div>
      <div className="space-y-2 min-h-[100px]">{children}</div>
    </div>
  )
}

function PipelineCardOverlay({ app }: { app: Application }) {
  return (
    <div className="bg-card border rounded-lg p-3 shadow-lg w-[240px]">
      <p className="text-sm font-medium text-foreground">{applicantLabel(app)}</p>
      <p className="text-xs text-muted-foreground mt-0.5">{app.program?.program_name ?? 'Program'}</p>
    </div>
  )
}

export default function PipelinePage({ embedded = false }: { embedded?: boolean }) {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const queryClient = useQueryClient()
  const [selectedProgram, setSelectedProgram] = useState<string>('')
  const [search, setSearch] = useState('')
  const [activeApp, setActiveApp] = useState<Application | null>(null)
  const readView = (): PipelineView => {
    const view = searchParams.get('view') as PipelineView | null
    if (view && PIPELINE_VIEWS.some(t => t.id === view)) return view
    const legacy = searchParams.get('tab') as PipelineView | null
    if (legacy && PIPELINE_VIEWS.some(t => t.id === legacy)) return legacy
    return 'board'
  }
  const [activeView, setActiveView] = useState<PipelineView>(readView)

  // Batch selection state
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [batchAction, setBatchAction] = useState<string | null>(null)
  const [batchItems, setBatchItems] = useState('')
  const [batchStatus, setBatchStatus] = useState('under_review')
  const [batchSlots, setBatchSlots] = useState<string[]>(['', '', ''])
  const [batchIvDuration, setBatchIvDuration] = useState('30')
  const [batchIvLocation, setBatchIvLocation] = useState('')

  const toggleSelect = (id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id); else next.add(id)
      return next
    })
  }
  const clearSelection = () => setSelectedIds(new Set())

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 8 } }))

  const programsQ = useQuery({ queryKey: ['institution-programs'], queryFn: getInstitutionPrograms })
  const programs: Program[] = Array.isArray(programsQ.data) ? programsQ.data : []

  const applicationsQ = useQuery({
    queryKey: ['pipeline-applications', selectedProgram],
    queryFn: () => getApplicationsByProgram(selectedProgram),
    enabled: !!selectedProgram,
  })
  const priorityQ = useQuery({
    queryKey: ['priority-queue', selectedProgram],
    queryFn: () => getReviewPriorityQueue(selectedProgram || undefined),
    enabled: activeView === 'priority',
  })
  const prioritized: PrioritizedApplication[] = Array.isArray(priorityQ.data) ? priorityQ.data : []

  const applications: Application[] = Array.isArray(applicationsQ.data) ? applicationsQ.data : []

  useEffect(() => {
    const next = readView()
    if (next !== activeView) setActiveView(next)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams])

  const grouped = useMemo(() => {
    const apps: Application[] = Array.isArray(applicationsQ.data) ? applicationsQ.data : []
    const filtered = apps.filter(a =>
      !search || (a.student_name ?? a.student_id).toLowerCase().includes(search.toLowerCase())
    )
    const map: Record<ColumnId, Application[]> = {
      submitted: [],
      under_review: [],
      interview: [],
      decision_made: [],
    }
    filtered.forEach(app => {
      const col = app.status as ColumnId
      if (map[col]) map[col].push(app)
      else map.submitted.push(app)
    })
    return map
  }, [applicationsQ.data, search])

  const reviewableApps = applications.filter(a =>
    (a.status === 'submitted' || a.status === 'under_review') && !a.decision
  )
  const filteredReviewableApps = reviewableApps.filter(a =>
    !search || (a.student_name ?? a.student_id).toLowerCase().includes(search.toLowerCase())
  )
  const filteredAllApps = applications.filter(a =>
    !search || (a.student_name ?? a.student_id).toLowerCase().includes(search.toLowerCase())
  )
  const selectedProgramName = programs.find(p => p.id === selectedProgram)?.program_name ?? ''

  const programOptions = programs.map(p => ({ value: p.id, label: p.program_name }))
  const goApplicant = (applicationId: string, tab?: string) => navigate(applicantUrl(applicationId, tab))

  const statusMut = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => updateApplicationStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipeline-applications', selectedProgram] })
      showToast('Status updated', 'success')
    },
    onError: () => {
      queryClient.invalidateQueries({ queryKey: ['pipeline-applications', selectedProgram] })
      showToast('Failed to update status', 'error')
    },
  })

  const selectedApps = applications.filter(a => selectedIds.has(a.id))

  const handleBatchResult = (result: BatchOperationResult) => {
    const msg = `${result.success_count} succeeded` + (result.failed_ids.length > 0 ? `, ${result.failed_ids.length} failed` : '')
    showToast(msg, result.failed_ids.length > 0 ? 'warning' : 'success')
    clearSelection()
    setBatchAction(null)
    setBatchItems('')
    setBatchSlots(['', '', ''])
    queryClient.invalidateQueries({ queryKey: ['pipeline-applications'] })
  }

  const batchAssignMut = useMutation({
    mutationFn: () => batchAssignReviewers(Array.from(selectedIds)),
    onSuccess: handleBatchResult,
    onError: () => showToast("We couldn't assign reviewers. Please try again.", 'error'),
  })
  const batchItemsMut = useMutation({
    mutationFn: () => batchRequestMissingItems(Array.from(selectedIds), batchItems.split(',').map(s => s.trim()).filter(Boolean)),
    onSuccess: handleBatchResult,
    onError: () => showToast("We couldn't request missing items. Please try again.", 'error'),
  })
  const batchStatusMut = useMutation({
    mutationFn: () => batchUpdateStatus(Array.from(selectedIds), batchStatus),
    onSuccess: handleBatchResult,
    onError: () => showToast("We couldn't update status. Please try again.", 'error'),
  })
  const batchInterviewMut = useMutation({
    mutationFn: () =>
      batchInviteInterviews(
        Array.from(selectedIds),
        '',
        'live',
        batchSlots.filter(Boolean).map(s => new Date(s).toISOString()),
        Number(batchIvDuration) || 30,
        batchIvLocation || undefined,
      ),
    onSuccess: handleBatchResult,
    onError: () => showToast("We couldn't schedule interviews. Please try again.", 'error'),
  })

  const handleDragStart = (event: DragStartEvent) => {
    const app = applications.find(a => a.id === event.active.id)
    setActiveApp(app ?? null)
  }

  const handleDragEnd = (event: DragEndEvent) => {
    setActiveApp(null)
    const { active, over } = event
    if (!over) return

    const appId = active.id as string
    const newStatus = over.id as string
    const app = applications.find(a => a.id === appId)
    if (!app || app.status === newStatus) return

    statusMut.mutate({ id: appId, status: newStatus })
  }

  const handleViewChange = (view: string) => {
    const nextView = view as PipelineView
    setActiveView(nextView)
    setSearchParams(prev => {
      const next = new URLSearchParams(prev)
      if (embedded) next.set('tab', 'pipeline')
      next.set('view', nextView)
      return next
    })
  }

  const reviewColumns = [
    {
      key: 'student_id',
      label: 'Applicant',
      render: (row: Application) => (
        <button
          onClick={() => goApplicant(row.id)}
          className="text-secondary hover:underline font-medium"
        >
          {applicantLabel(row)}
        </button>
      ),
    },
    {
      key: 'status',
      label: 'Current Stage',
      render: (row: Application) => (
        <Badge variant={(STATUS_COLORS[row.status] as any) ?? 'neutral'}>
          {row.status.replace('_', ' ')}
        </Badge>
      ),
    },
    {
      key: 'match_score',
      label: 'Match Score',
      render: (row: Application) => row.match_score != null ? formatScore(row.match_score) : '-',
    },
    {
      key: 'updated_at',
      label: 'Updated',
      render: (row: Application) => formatRelative(row.updated_at),
    },
  ]

  const interviewStageCount = filteredAllApps.filter(a => a.status === 'interview').length

  const toolbar = (
    <div className={`space-y-3 ${embedded ? '' : 'sticky top-14 z-[5] -mx-6 px-6 py-3 bg-muted/95 backdrop-blur supports-[backdrop-filter]:bg-muted/90 border-y border-border'}`}>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <p className="up-eyebrow text-muted-foreground">Pipeline</p>
        <span className="text-xs text-muted-foreground">View: Board · List · Needs Review · Priority</span>
      </div>
      <Tabs tabs={PIPELINE_VIEWS} activeTab={activeView} onChange={handleViewChange} />
      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
        <Select
          label={embedded ? undefined : 'Program'}
          options={programOptions}
          placeholder="Program"
          value={selectedProgram}
          onChange={e => setSelectedProgram(e.target.value)}
          className="w-full sm:w-72"
        />
        <div className="relative w-full sm:flex-1 sm:max-w-xs">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground/70" />
          <Input
            placeholder="Search"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>
    </div>
  )

  const body = (
    <div className="space-y-4">
      {toolbar}

      {!selectedProgram ? (
        <EmptyState title="Select a program" description="Choose a program above to manage its full admissions workflow." />
      ) : applicationsQ.isError ? (
        <QueryError detail="Couldn’t load applications." onRetry={() => applicationsQ.refetch()} />
      ) : applicationsQ.isLoading ? (
        <div className="flex gap-4">
          {PIPELINE_COLUMNS.map(col => (
            <div key={col.id} className="flex-1 space-y-2">
              <Skeleton className="h-6 w-24" />
              <Skeleton className="h-20" />
              <Skeleton className="h-20" />
            </div>
          ))}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
            <Card className="p-3">
              <p className="text-xs text-muted-foreground">Program</p>
              <p className="text-sm font-semibold text-foreground truncate">{selectedProgramName}</p>
            </Card>
            <Card className="p-3">
              <p className="text-xs text-muted-foreground">Total Applications</p>
              <p className="text-xl font-semibold text-foreground">{applications.length}</p>
            </Card>
            <Card className="p-3">
              <p className="text-xs text-muted-foreground">Needs Review</p>
              <p className="text-xl font-semibold text-warning">{reviewableApps.length}</p>
            </Card>
            <Card className="p-3">
              <p className="text-xs text-muted-foreground">Interview Stage</p>
              <p className="text-xl font-bold text-secondary">{interviewStageCount}</p>
            </Card>
          </div>

          {activeView === 'board' && (
            <DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
              <div className="flex gap-4 overflow-x-auto pb-4">
                {PIPELINE_COLUMNS.map(col => (
                  <DroppableColumn key={col.id} id={col.id} label={`${col.label} (${grouped[col.id].length})`} color={col.color}>
                    {grouped[col.id].length === 0 ? (
                      <p className="text-xs text-muted-foreground/70 text-center py-4">No applications</p>
                    ) : (
                      grouped[col.id].map(app => (
                        <DraggableCard
                          key={app.id}
                          app={app}
                          selected={selectedIds.has(app.id)}
                          onToggleSelect={toggleSelect}
                          onClick={() => goApplicant(app.id)}
                          onGenerateOffer={() => goApplicant(app.id, 'decision')}
                        />
                      ))
                    )}
                  </DroppableColumn>
                ))}
              </div>

              <DragOverlay>
                {activeApp ? <PipelineCardOverlay app={activeApp} /> : null}
              </DragOverlay>
            </DndContext>
          )}

          {activeView === 'review' && (
            <Card className="p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-foreground">Needs Review ({filteredReviewableApps.length})</h3>
                <Badge variant="warning" className="flex items-center gap-1">
                  <ClipboardCheck size={12} />
                  Priority Queue
                </Badge>
              </div>
              {filteredReviewableApps.length === 0 ? (
                <EmptyState title="No pending reviews" description="All applications in this program are currently reviewed." />
              ) : (
                <Table columns={reviewColumns} data={filteredReviewableApps} onRowClick={(row) => goApplicant(row.id)} pageSize={50} />
              )}
            </Card>
          )}

          {activeView === 'list' && (
            <Card className="p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-foreground">All Applications ({filteredAllApps.length})</h3>
                <Badge variant="info" className="flex items-center gap-1">
                  <List size={12} />
                  Unified View
                </Badge>
              </div>
              {filteredAllApps.length === 0 ? (
                <EmptyState title="No applications found" description="Try clearing search or checking another program." />
              ) : (
                <Table columns={reviewColumns} data={filteredAllApps} onRowClick={(row) => goApplicant(row.id)} pageSize={50} />
              )}
            </Card>
          )}

          {activeView === 'priority' && (
            <div className="space-y-2">
              {priorityQ.isError ? (
                <QueryError detail="Couldn’t load the priority queue." onRetry={() => priorityQ.refetch()} />
              ) : priorityQ.isLoading ? (
                <Skeleton className="h-40" />
              ) : prioritized.length === 0 ? (
                <EmptyState icon={<Zap size={40} />} title="No applications to prioritize" description="Applications needing review will be ranked here by urgency." />
              ) : (
                prioritized.map((p, i) => (
                  <Card key={p.application_id} className="p-4 cursor-pointer hover:shadow-md transition-shadow" onClick={() => goApplicant(p.application_id)}>
                    <div className="flex items-center gap-4">
                      <div className={`flex items-center justify-center w-10 h-10 rounded-full shrink-0 font-bold text-white text-sm ${
                        p.priority_score >= 70 ? 'bg-error' : p.priority_score >= 40 ? 'bg-warning' : 'bg-success'
                      }`}>
                        {Math.round(p.priority_score)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-medium text-foreground">#{i + 1} — {applicantLabel(p)}</span>
                          <Badge variant="info">{p.program_name}</Badge>
                          <Badge variant="neutral">{p.status}</Badge>
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {p.priority_reasons.map((r, j) => (
                            <span key={j} className="text-xs bg-muted text-muted-foreground px-1.5 py-0.5 rounded">{r}</span>
                          ))}
                        </div>
                      </div>
                      <div className="text-right shrink-0">
                        {p.deadline_days != null && (
                          <div className={`flex items-center gap-1 text-xs font-medium ${p.deadline_days <= 7 ? 'text-error' : p.deadline_days <= 14 ? 'text-warning' : 'text-muted-foreground'}`}>
                            <Clock size={12} />
                            {p.deadline_days <= 0 ? 'Past due' : `${p.deadline_days}d left`}
                          </div>
                        )}
                        {p.match_score != null && (
                          <p className="text-xs text-muted-foreground/70 mt-0.5">Match: {(p.match_score * 100).toFixed(0)}%</p>
                        )}
                        <p className="text-xs text-muted-foreground/70">{p.assigned_count === 0 ? 'Unassigned' : `${p.assigned_count} reviewer(s)`}</p>
                      </div>
                    </div>
                  </Card>
                ))
              )}
            </div>
          )}

          {interviewStageCount > 0 && activeView === 'board' && (
            <p className="text-xs text-muted-foreground">
              {interviewStageCount} in interview stage —{' '}
              <button type="button" className="text-secondary hover:underline" onClick={() => navigate(admissionsUrl('interviews'))}>
                open Interviews tab
              </button>
            </p>
          )}
        </>
      )}

      {/* Batch Action Bar */}
      {selectedIds.size > 0 && (
        <div className="fixed bottom-0 left-0 right-0 bg-card border-t shadow-lg px-6 py-3 flex items-center justify-between z-50">
          <span className="text-sm font-medium flex items-center gap-2">
            <CheckSquare size={16} className="text-secondary" />
            {selectedIds.size} selected
          </span>
          <div className="flex gap-2">
            <Button size="sm" variant="secondary" onClick={() => setBatchAction('assign')}>Assign reviewers</Button>
            <Button size="sm" variant="secondary" onClick={() => setBatchAction('request-items')}>Request missing items</Button>
            <Button size="sm" variant="secondary" onClick={() => setBatchAction('interview')}>Invite interviews</Button>
            <Button size="sm" variant="secondary" onClick={() => setBatchAction('status')}>Update status</Button>
            <Button size="sm" variant="secondary" onClick={() => setBatchAction('decision')}>Release decisions</Button>
            <Button size="sm" variant="ghost" onClick={clearSelection}>Clear</Button>
          </div>
        </div>
      )}

      {/* Batch Assign Modal */}
      <Modal isOpen={batchAction === 'assign'} onClose={() => setBatchAction(null)} title="Batch Assign Reviewers">
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">Auto-assign reviewers to {selectedIds.size} application(s).</p>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setBatchAction(null)}>Cancel</Button>
            <Button onClick={() => batchAssignMut.mutate()} disabled={batchAssignMut.isPending}>
              {batchAssignMut.isPending ? 'Assigning...' : `Assign to ${selectedIds.size} apps`}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Batch Request Items Modal */}
      <Modal isOpen={batchAction === 'request-items'} onClose={() => setBatchAction(null)} title="Batch Request Missing Items">
        <div className="space-y-4">
          <Textarea label="Missing Items (comma-separated)" value={batchItems} onChange={e => setBatchItems(e.target.value)} rows={3} placeholder="e.g. Transcript, Letter of Recommendation, Test Scores" />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setBatchAction(null)}>Cancel</Button>
            <Button onClick={() => batchItemsMut.mutate()} disabled={batchItemsMut.isPending || !batchItems.trim()}>
              {batchItemsMut.isPending ? 'Requesting...' : `Request from ${selectedIds.size} apps`}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Batch Interview Modal */}
      <Modal
        isOpen={batchAction === 'interview'}
        onClose={() => { setBatchAction(null); setBatchSlots(['', '', '']) }}
        title="Batch Schedule Interviews"
      >
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Propose a live interview to {selectedIds.size} application(s). Offer at least three times so applicants can choose (Spec 33 §5).
          </p>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Proposed times</label>
            {batchSlots.map((t, i) => (
              <div key={i} className="flex items-center gap-2 mb-2">
                <Input
                  type="datetime-local"
                  value={t}
                  onChange={e => setBatchSlots(batchSlots.map((s, idx) => (idx === i ? e.target.value : s)))}
                  className="flex-1"
                />
                {batchSlots.length > 1 && (
                  <button
                    type="button"
                    onClick={() => setBatchSlots(batchSlots.filter((_, idx) => idx !== i))}
                    className="p-1 text-muted-foreground hover:text-error transition-colors"
                    aria-label="Remove time"
                  >
                    <Trash2 size={16} />
                  </button>
                )}
              </div>
            ))}
            <Button variant="ghost" size="sm" onClick={() => setBatchSlots([...batchSlots, ''])} className="flex items-center gap-1">
              <Plus size={14} /> Add time
            </Button>
          </div>
          <Input label="Duration (minutes)" type="number" value={batchIvDuration} onChange={e => setBatchIvDuration(e.target.value)} />
          <Input
            label="Location or meeting link"
            value={batchIvLocation}
            onChange={e => setBatchIvLocation(e.target.value)}
            placeholder="Zoom link, platform URL, or campus address"
          />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => { setBatchAction(null); setBatchSlots(['', '', '']) }}>Cancel</Button>
            <Button
              onClick={() => batchInterviewMut.mutate()}
              disabled={batchInterviewMut.isPending || batchSlots.filter(Boolean).length < 3}
            >
              {batchInterviewMut.isPending ? 'Scheduling...' : `Propose to ${selectedIds.size}`}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Batch Status Modal */}
      <Modal isOpen={batchAction === 'status'} onClose={() => setBatchAction(null)} title="Batch Update Status">
        <div className="space-y-4">
          <Select label="New Status" options={[
            { value: 'submitted', label: 'Applied' },
            { value: 'under_review', label: 'Under Review' },
            { value: 'interview', label: 'Interview' },
            { value: 'decision_made', label: 'Decision Made' },
          ]} value={batchStatus} onChange={e => setBatchStatus(e.target.value)} />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setBatchAction(null)}>Cancel</Button>
            <Button onClick={() => batchStatusMut.mutate()} disabled={batchStatusMut.isPending}>
              {batchStatusMut.isPending ? 'Updating...' : `Update ${selectedIds.size} apps`}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Batch Release Decisions (spec 34 §5) */}
      <BatchReleaseModal
        isOpen={batchAction === 'decision'}
        onClose={() => setBatchAction(null)}
        selectedApps={selectedApps}
        onDone={() => {
          clearSelection()
          queryClient.invalidateQueries({ queryKey: ['pipeline-applications'] })
        }}
      />
    </div>
  )

  if (embedded) return body

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-bold text-foreground">Applications Workspace</h1>
      {body}
    </div>
  )
}
