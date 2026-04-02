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
import { Search, GripVertical, ClipboardCheck, List, Video } from 'lucide-react'
import { getInstitutionPrograms } from '../../api/institutions'
import { getApplicationsByProgram, updateApplicationStatus } from '../../api/applications-admin'
import { getInstitutionInterviews } from '../../api/interviews-admin'
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
import type { Application, Program } from '../../types'

const PIPELINE_COLUMNS = [
  { id: 'submitted', label: 'Applied', color: 'bg-blue-500' },
  { id: 'under_review', label: 'Under Review', color: 'bg-yellow-500' },
  { id: 'interview', label: 'Interview', color: 'bg-purple-500' },
  { id: 'decision_made', label: 'Decision', color: 'bg-orange-500' },
] as const

type ColumnId = typeof PIPELINE_COLUMNS[number]['id']
type PipelineTab = 'board' | 'review' | 'list' | 'interviews'

function DraggableCard({ app, onClick }: { app: Application; onClick: () => void }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({ id: app.id })
  const style = transform ? { transform: `translate(${transform.x}px, ${transform.y}px)` } : undefined

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`bg-white border rounded-lg p-3 cursor-pointer hover:shadow-md transition-shadow ${isDragging ? 'opacity-50' : ''}`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-gray-900 truncate">Applicant {app.student_id.slice(0, 8)}</p>
          <p className="text-xs text-gray-500 mt-0.5">{app.program?.program_name ?? 'Program'}</p>
        </div>
        <div {...listeners} {...attributes} className="p-1 cursor-grab text-gray-400">
          <GripVertical size={14} />
        </div>
      </div>
      <div className="flex items-center justify-between mt-2">
        {app.match_score != null && (
          <span className="text-xs font-medium text-indigo-600">{formatScore(app.match_score / 100)}</span>
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
      className={`flex-1 min-w-[240px] rounded-lg p-3 transition-colors ${isOver ? 'bg-indigo-50 ring-2 ring-indigo-300' : 'bg-gray-50'}`}
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
  const initialTab = (searchParams.get('tab') as PipelineTab) || 'board'
  const [activeTab, setActiveTab] = useState<PipelineTab>(initialTab)

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 8 } }))

  const programsQ = useQuery({ queryKey: ['institution-programs'], queryFn: getInstitutionPrograms })
  const programs: Program[] = Array.isArray(programsQ.data) ? programsQ.data : []

  const applicationsQ = useQuery({
    queryKey: ['pipeline-applications', selectedProgram],
    queryFn: () => getApplicationsByProgram(selectedProgram),
    enabled: !!selectedProgram,
  })
  const applications: Application[] = Array.isArray(applicationsQ.data) ? applicationsQ.data : []
  const interviewsQ = useQuery({
    queryKey: ['institution-interviews', selectedProgram],
    queryFn: () => getInstitutionInterviews(),
    enabled: activeTab === 'interviews',
  })

  useEffect(() => {
    const tabParam = (searchParams.get('tab') as PipelineTab) || 'board'
    if (tabParam !== activeTab) setActiveTab(tabParam)
  }, [activeTab, searchParams])

  const grouped = useMemo(() => {
    const filtered = applications.filter(a =>
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
  }, [applications, search])

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
      next.set('tab', nextTab)
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
          className="text-indigo-600 hover:underline font-medium"
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
      render: (row: Application) => row.match_score != null ? formatScore(row.match_score / 100) : '-',
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
    </div>
  )
}
