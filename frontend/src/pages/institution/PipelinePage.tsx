import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
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
import { Search, GripVertical } from 'lucide-react'
import { getInstitutionPrograms } from '../../api/institutions'
import { getApplicationsByProgram, updateApplicationStatus } from '../../api/applications-admin'
import { showToast } from '../../stores/toast-store'
import Badge from '../../components/ui/Badge'
import Select from '../../components/ui/Select'
import Input from '../../components/ui/Input'
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
          <p className="text-sm font-medium text-gray-900 truncate">{app.student_id.slice(0, 8)}...</p>
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

function DroppableColumn({ id, label, color, children }: { id: string; label: string; color: string; children: React.ReactNode }) {
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
      <p className="text-sm font-medium text-gray-900">{app.student_id.slice(0, 8)}...</p>
      <p className="text-xs text-gray-500 mt-0.5">{app.program?.program_name ?? 'Program'}</p>
    </div>
  )
}

export default function PipelinePage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [selectedProgram, setSelectedProgram] = useState<string>('')
  const [search, setSearch] = useState('')
  const [activeApp, setActiveApp] = useState<Application | null>(null)

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 8 } }))

  const programsQ = useQuery({ queryKey: ['institution-programs'], queryFn: getInstitutionPrograms })
  const programs: Program[] = Array.isArray(programsQ.data) ? programsQ.data : []

  const applicationsQ = useQuery({
    queryKey: ['pipeline-applications', selectedProgram],
    queryFn: () => getApplicationsByProgram(selectedProgram),
    enabled: !!selectedProgram,
  })
  const applications: Application[] = Array.isArray(applicationsQ.data) ? applicationsQ.data : []

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

  const programOptions = programs.map(p => ({ value: p.id, label: p.program_name }))

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

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Pipeline</h1>
      </div>

      <div className="flex items-center gap-4">
        <Select
          options={programOptions}
          placeholder="Select Program"
          value={selectedProgram}
          onChange={e => setSelectedProgram(e.target.value)}
          className="w-64"
        />
        <div className="relative flex-1 max-w-xs">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <Input
            placeholder="Search students..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {!selectedProgram ? (
        <EmptyState title="Select a program" description="Choose a program above to view its application pipeline." />
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
        <DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
          <div className="flex gap-4 overflow-x-auto pb-4">
            {PIPELINE_COLUMNS.map(col => (
              <DroppableColumn key={col.id} id={col.id} label={col.label} color={col.color}>
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
    </div>
  )
}
