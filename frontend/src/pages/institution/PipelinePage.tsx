import { useState, useMemo, useEffect, type ReactNode } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
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
import { Search, GripVertical, ClipboardCheck, List, Video, CheckSquare, Zap, Clock } from 'lucide-react'
import { getInstitutionPrograms } from '../../api/institutions'
import { getApplicationsByProgram, updateApplicationStatus, batchRequestMissingItems, batchUpdateStatus, batchReleaseDecision } from '../../api/applications-admin'
import { batchAssignReviewers, getReviewPriorityQueue } from '../../api/reviews'
import { getInstitutionInterviews, batchInviteInterviews } from '../../api/interviews-admin'
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
  { id: 'submitted', label: 'Applied', color: 'bg-blue-500' },
  { id: 'under_review', label: 'Under Review', color: 'bg-yellow-500' },
  { id: 'interview', label: 'Interview', color: 'bg-purple-500' },
  { id: 'decision_made', label: 'Decision', color: 'bg-orange-500' },
] as const

type ColumnId = typeof PIPELINE_COLUMNS[number]['id']
type PipelineTab = 'board' | 'review' | 'list' | 'interviews' | 'priority'

function DraggableCard({ app, onClick, selected, onToggleSelect }: {
  app: Application; onClick: () => void; selected?: boolean; onToggleSelect?: (id: string) => void
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({ id: app.id })
  const style = transform ? { transform: `translate(${transform.x}px, ${transform.y}px)` } : undefined

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`bg-white border rounded-lg p-3 cursor-pointer hover:shadow-md transition-shadow ${isDragging ? 'opacity-50' : ''} ${selected ? 'ring-2 ring-brand-slate-500 border-brand-slate-300' : ''}`}
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
              className="mt-1 rounded border-gray-300"
            />
          )}
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-gray-900 truncate">Applicant {app.student_id.slice(0, 8)}</p>
            <p className="text-xs text-gray-500 mt-0.5">{app.program?.program_name ?? 'Program'}</p>
          </div>
        </div>
        <div {...listeners} {...attributes} className="p-1 cursor-grab text-gray-400">
          <GripVertical size={14} />
        </div>
      </div>
      <div className="flex items-center justify-between mt-2">
        {app.match_score != null && (
          <span className="text-xs font-medium text-brand-slate-600">{formatScore(app.match_score)}</span>
        )}
        <span className="text-xs text-gray-400">{formatRelative(app.updated_at)}</span>
      </div>
      {app.decision && (
        <Badge variant={(STATUS_COLORS[app.decision] as any) ?? 'neutral'} className="mt-1.5">
          {app.decision}
        </Badge>
      )}
    </div>
  )
}

function DroppableColumn({ id, label, color, children }: { id: string; label: string; color: string; children: ReactNode }) {
  const { setNodeRef, isOver } = useDroppable({ id })
  return (
    <div
      ref={setNodeRef}
      className={`flex-1 min-w-[240px] rounded-lg p-3 transition-colors ${isOver ? 'bg-brand-slate-50 ring-2 ring-brand-slate-300' : 'bg-gray-50'}`}
    >
      <div className="flex items-center gap-2 mb-3">
        <div className={`w-3 h-3 rounded-full ${color}`} />
        <h3 className="text-sm font-semibold text-gray-700">{label}</h3>
      </div>
      <div className="space-y-2 min-h-[100px]">{children}</div>
    </div>
  )
}

function PipelineCardOverlay({ app }: { app: Application }) {
  return (
    <div className="bg-white border rounded-lg p-3 shadow-lg w-[240px]">
      <p className="text-sm font-medium text-gray-900">Applicant {app.student_id.slice(0, 8)}</p>
      <p className="text-xs text-gray-500 mt-0.5">{app.program?.program_name ?? 'Program'}</p>
    </div>
  )
}

export default function PipelinePage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const queryClient = useQueryClient()
  const [selectedProgram, setSelectedProgram] = useState<string>('')
  const [search, setSearch] = useState('')
  const [activeApp, setActiveApp] = useState<Application | null>(null)
  const initialTab = (searchParams.get('subtab') as PipelineTab) || 'board'
  const [activeTab, setActiveTab] = useState<PipelineTab>(initialTab)

  // Batch selection state
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [batchAction, setBatchAction] = useState<string | null>(null)
  const [batchItems, setBatchItems] = useState('')
  const [batchStatus, setBatchStatus] = useState('under_review')
  const [batchDecision, setBatchDecision] = useState('admitted')
  const [batchNotes, setBatchNotes] = useState('')

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
  const interviewsQ = useQuery({
    queryKey: ['institution-interviews', selectedProgram],
    queryFn: () => getInstitutionInterviews(),
    enabled: activeTab === 'interviews',
  })

  const priorityQ = useQuery({
    queryKey: ['priority-queue', selectedProgram],
    queryFn: () => getReviewPriorityQueue(selectedProgram || undefined),
    enabled: activeTab === 'priority',
  })
  const prioritized: PrioritizedApplication[] = Array.isArray(priorityQ.data) ? priorityQ.data : []

  const applications: Application[] = Array.isArray(applicationsQ.data) ? applicationsQ.data : []

  useEffect(() => {
    const tabParam = (searchParams.get('tab') as PipelineTab) || 'board'
    if (tabParam !== activeTab) setActiveTab(tabParam)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams])

  const grouped = useMemo(() => {
    const apps: Application[] = Array.isArray(applicationsQ.data) ? applicationsQ.data : []
    const filtered = apps.filter(a =>
      !search || a.student_id.toLowerCase().includes(search.toLowerCase())
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
    !search || a.student_id.toLowerCase().includes(search.toLowerCase())
  )
  const filteredAllApps = applications.filter(a =>
    !search || a.student_id.toLowerCase().includes(search.toLowerCase())
  )
  const interviews = Array.isArray(interviewsQ.data) ? interviewsQ.data : []
  const interviewCandidates = filteredAllApps.filter(a => a.status === 'interview')
  const selectedProgramName = programs.find(p => p.id === selectedProgram)?.program_name ?? ''

  const programOptions = programs.map(p => ({ value: p.id, label: p.program_name }))
  const tabs = [
    { id: 'board', label: 'Board' },
    { id: 'priority', label: 'Priority Queue' },
    { id: 'review', label: 'Needs Review' },
    { id: 'list', label: 'All Applications' },
    { id: 'interviews', label: 'Interviews' },
  ]

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

  const handleBatchResult = (result: BatchOperationResult) => {
    const msg = `${result.success_count} succeeded` + (result.failed_ids.length > 0 ? `, ${result.failed_ids.length} failed` : '')
    showToast(msg, result.failed_ids.length > 0 ? 'warning' : 'success')
    clearSelection()
    setBatchAction(null)
    setBatchItems('')
    setBatchNotes('')
    queryClient.invalidateQueries({ queryKey: ['pipeline-applications'] })
  }

  const batchAssignMut = useMutation({
    mutationFn: () => batchAssignReviewers(Array.from(selectedIds)),
    onSuccess: handleBatchResult,
  })
  const batchItemsMut = useMutation({
    mutationFn: () => batchRequestMissingItems(Array.from(selectedIds), batchItems.split(',').map(s => s.trim()).filter(Boolean)),
    onSuccess: handleBatchResult,
  })
  const batchStatusMut = useMutation({
    mutationFn: () => batchUpdateStatus(Array.from(selectedIds), batchStatus),
    onSuccess: handleBatchResult,
  })
  const batchDecisionMut = useMutation({
    mutationFn: () => batchReleaseDecision(Array.from(selectedIds), batchDecision, batchNotes || undefined),
    onSuccess: handleBatchResult,
  })
  const batchInterviewMut = useMutation({
    mutationFn: () => batchInviteInterviews(Array.from(selectedIds), '', 'standard', [new Date().toISOString()]),
    onSuccess: handleBatchResult,
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

  const handleTabChange = (tab: string) => {
    const nextTab = tab as PipelineTab
    setActiveTab(nextTab)
    setSearchParams(prev => {
      const next = new URLSearchParams(prev)
      next.set('subtab', nextTab)
      return next
    })
  }

  const reviewColumns = [
    {
      key: 'student_id',
      label: 'Applicant',
      render: (row: Application) => (
        <button
          onClick={() => navigate(`/i/pipeline/${row.id}`)}
          className="text-brand-slate-600 hover:underline font-medium"
        >
          Applicant {row.student_id.slice(0, 8)}
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

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Applications Workspace</h1>
      </div>

      <div className="sticky top-14 z-[5] -mx-6 px-6 py-3 bg-gray-50/95 backdrop-blur supports-[backdrop-filter]:bg-gray-50/90 border-y border-gray-100">
        <div className="space-y-3">
          <Tabs tabs={tabs} activeTab={activeTab} onChange={handleTabChange} />
          <div className="flex flex-col sm:flex-row sm:items-center gap-3">
            <Select
              options={programOptions}
              placeholder="Select Program to Operate"
              value={selectedProgram}
              onChange={e => setSelectedProgram(e.target.value)}
              className="w-full sm:w-72"
            />
            <div className="relative w-full sm:flex-1 sm:max-w-xs">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <Input
                placeholder="Search by applicant ID..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
          </div>
        </div>
      </div>

      {!selectedProgram ? (
        <EmptyState title="Select a program" description="Choose a program above to manage its full admissions workflow." />
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
              <p className="text-xs text-gray-500">Program</p>
              <p className="text-sm font-semibold text-gray-900 truncate">{selectedProgramName}</p>
            </Card>
            <Card className="p-3">
              <p className="text-xs text-gray-500">Total Applications</p>
              <p className="text-xl font-semibold text-gray-900">{applications.length}</p>
            </Card>
            <Card className="p-3">
              <p className="text-xs text-gray-500">Needs Review</p>
              <p className="text-xl font-semibold text-amber-700">{reviewableApps.length}</p>
            </Card>
            <Card className="p-3">
              <p className="text-xs text-gray-500">Interview Stage</p>
              <p className="text-xl font-semibold text-purple-700">{interviewCandidates.length}</p>
            </Card>
          </div>

          {activeTab === 'board' && (
            <DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
              <div className="flex gap-4 overflow-x-auto pb-4">
                {PIPELINE_COLUMNS.map(col => (
                  <DroppableColumn key={col.id} id={col.id} label={`${col.label} (${grouped[col.id].length})`} color={col.color}>
                    {grouped[col.id].length === 0 ? (
                      <p className="text-xs text-gray-400 text-center py-4">No applications</p>
                    ) : (
                      grouped[col.id].map(app => (
                        <DraggableCard
                          key={app.id}
                          app={app}
                          selected={selectedIds.has(app.id)}
                          onToggleSelect={toggleSelect}
                          onClick={() => navigate(`/i/pipeline/${app.id}`)}
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

          {activeTab === 'review' && (
            <Card className="p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-900">Needs Review ({filteredReviewableApps.length})</h3>
                <Badge variant="warning" className="flex items-center gap-1">
                  <ClipboardCheck size={12} />
                  Priority Queue
                </Badge>
              </div>
              {filteredReviewableApps.length === 0 ? (
                <EmptyState title="No pending reviews" description="All applications in this program are currently reviewed." />
              ) : (
                <Table columns={reviewColumns} data={filteredReviewableApps} onRowClick={(row) => navigate(`/i/pipeline/${row.id}`)} />
              )}
            </Card>
          )}

          {activeTab === 'list' && (
            <Card className="p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-900">All Applications ({filteredAllApps.length})</h3>
                <Badge variant="info" className="flex items-center gap-1">
                  <List size={12} />
                  Unified View
                </Badge>
              </div>
              {filteredAllApps.length === 0 ? (
                <EmptyState title="No applications found" description="Try clearing search or checking another program." />
              ) : (
                <Table columns={reviewColumns} data={filteredAllApps} onRowClick={(row) => navigate(`/i/pipeline/${row.id}`)} />
              )}
            </Card>
          )}

          {activeTab === 'priority' && (
            <div className="space-y-2">
              {priorityQ.isLoading ? (
                <Skeleton className="h-40" />
              ) : prioritized.length === 0 ? (
                <EmptyState icon={<Zap size={40} />} title="No applications to prioritize" description="Applications needing review will be ranked here by urgency." />
              ) : (
                prioritized.map((p, i) => (
                  <Card key={p.application_id} className="p-4 cursor-pointer hover:shadow-md transition-shadow" onClick={() => navigate(`/i/pipeline/${p.application_id}`)}>
                    <div className="flex items-center gap-4">
                      <div className="flex items-center justify-center w-10 h-10 rounded-full shrink-0 font-bold text-white text-sm"
                        style={{ backgroundColor: p.priority_score >= 70 ? '#ef4444' : p.priority_score >= 40 ? '#f59e0b' : '#22c55e' }}>
                        {Math.round(p.priority_score)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-medium text-gray-900">#{i + 1} — Applicant {p.student_id.slice(0, 8)}</span>
                          <Badge variant="info">{p.program_name}</Badge>
                          <Badge variant="neutral">{p.status}</Badge>
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {p.priority_reasons.map((r, j) => (
                            <span key={j} className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">{r}</span>
                          ))}
                        </div>
                      </div>
                      <div className="text-right shrink-0">
                        {p.deadline_days != null && (
                          <div className={`flex items-center gap-1 text-xs font-medium ${p.deadline_days <= 7 ? 'text-red-600' : p.deadline_days <= 14 ? 'text-amber-600' : 'text-gray-500'}`}>
                            <Clock size={12} />
                            {p.deadline_days <= 0 ? 'Past due' : `${p.deadline_days}d left`}
                          </div>
                        )}
                        {p.match_score != null && (
                          <p className="text-xs text-gray-400 mt-0.5">Match: {(p.match_score * 100).toFixed(0)}%</p>
                        )}
                        <p className="text-xs text-gray-400">{p.assigned_count === 0 ? 'Unassigned' : `${p.assigned_count} reviewer(s)`}</p>
                      </div>
                    </div>
                  </Card>
                ))
              )}
            </div>
          )}

          {activeTab === 'interviews' && (
            <Card className="p-4 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-gray-900">Interview Pipeline ({interviewCandidates.length})</h3>
                <Button variant="secondary" size="sm" onClick={() => navigate('/i/interviews')} className="flex items-center gap-2">
                  <Video size={14} />
                  Open Interview Scheduler
                </Button>
              </div>
              <p className="text-sm text-gray-600">
                Candidates in the interview stage are listed here for quick triage. Use Interview Scheduler for availability and scoring.
              </p>
              {interviewCandidates.length === 0 ? (
                <EmptyState title="No interview-stage candidates" description="Move candidates to Interview from Board to schedule next steps." />
              ) : (
                <Table columns={reviewColumns} data={interviewCandidates} onRowClick={(row) => navigate(`/i/pipeline/${row.id}`)} />
              )}
              {interviewsQ.isLoading ? (
                <p className="text-xs text-gray-500">Loading interview schedule data...</p>
              ) : (
                <p className="text-xs text-gray-500">Total interview records in system: {interviews.length}</p>
              )}
            </Card>
          )}
        </>
      )}

      {/* Batch Action Bar */}
      {selectedIds.size > 0 && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t shadow-lg px-6 py-3 flex items-center justify-between z-50">
          <span className="text-sm font-medium flex items-center gap-2">
            <CheckSquare size={16} className="text-brand-slate-600" />
            {selectedIds.size} selected
          </span>
          <div className="flex gap-2">
            <Button size="sm" variant="secondary" onClick={() => setBatchAction('assign')}>Assign Reviewer</Button>
            <Button size="sm" variant="secondary" onClick={() => setBatchAction('request-items')}>Request Items</Button>
            <Button size="sm" variant="secondary" onClick={() => setBatchAction('interview')}>Schedule Interview</Button>
            <Button size="sm" variant="secondary" onClick={() => setBatchAction('status')}>Update Status</Button>
            <Button size="sm" variant="secondary" onClick={() => setBatchAction('decision')}>Release Decision</Button>
            <Button size="sm" variant="ghost" onClick={clearSelection}>Clear</Button>
          </div>
        </div>
      )}

      {/* Batch Assign Modal */}
      <Modal isOpen={batchAction === 'assign'} onClose={() => setBatchAction(null)} title="Batch Assign Reviewers">
        <div className="space-y-4">
          <p className="text-sm text-gray-600">Auto-assign reviewers to {selectedIds.size} application(s).</p>
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
      <Modal isOpen={batchAction === 'interview'} onClose={() => setBatchAction(null)} title="Batch Schedule Interviews">
        <div className="space-y-4">
          <p className="text-sm text-gray-600">Schedule standard interviews for {selectedIds.size} application(s).</p>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setBatchAction(null)}>Cancel</Button>
            <Button onClick={() => batchInterviewMut.mutate()} disabled={batchInterviewMut.isPending}>
              {batchInterviewMut.isPending ? 'Scheduling...' : `Schedule ${selectedIds.size} interviews`}
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

      {/* Batch Decision Modal */}
      <Modal isOpen={batchAction === 'decision'} onClose={() => setBatchAction(null)} title="Batch Release Decision">
        <div className="space-y-4">
          <Select label="Decision" options={[
            { value: 'admitted', label: 'Admitted' },
            { value: 'rejected', label: 'Rejected' },
            { value: 'waitlisted', label: 'Waitlisted' },
            { value: 'deferred', label: 'Deferred' },
          ]} value={batchDecision} onChange={e => setBatchDecision(e.target.value)} />
          <Textarea label="Notes (optional)" value={batchNotes} onChange={e => setBatchNotes(e.target.value)} rows={3} placeholder="Decision notes for all selected applications..." />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setBatchAction(null)}>Cancel</Button>
            <Button onClick={() => batchDecisionMut.mutate()} disabled={batchDecisionMut.isPending}>
              {batchDecisionMut.isPending ? 'Releasing...' : `Release to ${selectedIds.size} apps`}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
