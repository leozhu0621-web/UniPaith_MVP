import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Calendar, Plus, Trash2 } from 'lucide-react'
import { getInstitutionPrograms } from '../../api/institutions'
import { getInstitutionInterviews, proposeInterview, completeInterview, scoreInterview } from '../../api/interviews-admin'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Tabs from '../../components/ui/Tabs'
import Table from '../../components/ui/Table'
import Modal from '../../components/ui/Modal'
import Input from '../../components/ui/Input'
import Select from '../../components/ui/Select'
import Textarea from '../../components/ui/Textarea'
import EmptyState from '../../components/ui/EmptyState'
import Skeleton from '../../components/ui/Skeleton'
import InstitutionPageHeader from '../../components/institution/InstitutionPageHeader'
import { showToast } from '../../stores/toast-store'
import { formatDateTime } from '../../utils/format'
import { STATUS_COLORS, INTERVIEW_TYPES } from '../../utils/constants'
import type { Interview } from '../../types'

export default function InterviewsPage() {
  const [activeTab, setActiveTab] = useState('upcoming')
  const [showScheduleModal, setShowScheduleModal] = useState(false)
  const [showScoreModal, setShowScoreModal] = useState(false)
  const [selectedInterview, setSelectedInterview] = useState<string | null>(null)

  // Schedule form state
  const [schedAppId, setSchedAppId] = useState('')
  const [schedType, setSchedType] = useState('video')
  const [schedTimes, setSchedTimes] = useState<string[]>([''])
  const [schedDuration, setSchedDuration] = useState('60')
  const [schedLocation, setSchedLocation] = useState('')

  // Score form state
  const [scoreNotes, setScoreNotes] = useState('')
  const [scoreRec, setScoreRec] = useState('')
  const scoreCriteria: Record<string, number> = {}

  const qc = useQueryClient()

  const interviewsQ = useQuery({
    queryKey: ['institution-interviews'],
    queryFn: () => getInstitutionInterviews(),
  })
  const interviews: Interview[] = Array.isArray(interviewsQ.data) ? interviewsQ.data : []

  const programsQ = useQuery({ queryKey: ['institution-programs'], queryFn: getInstitutionPrograms })
  void programsQ

  const tabs = [
    { id: 'upcoming', label: 'Upcoming' },
    { id: 'completed', label: 'Completed' },
    { id: 'all', label: 'All' },
  ]

  const filteredInterviews = interviews.filter(i => {
    if (activeTab === 'upcoming') return ['proposed', 'confirmed'].includes(i.status)
    if (activeTab === 'completed') return i.status === 'completed'
    return true
  })
  const confirmedCount = interviews.filter(i => i.status === 'confirmed').length
  const completedCount = interviews.filter(i => i.status === 'completed').length
  const proposedCount = interviews.filter(i => i.status === 'proposed').length

  const proposeMut = useMutation({
    mutationFn: proposeInterview,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['institution-interviews'] })
      showToast('Interview proposed', 'success')
      setShowScheduleModal(false)
    },
    onError: () => showToast('Failed to propose interview', 'error'),
  })

  const completeMut = useMutation({
    mutationFn: completeInterview,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['institution-interviews'] })
      showToast('Interview completed', 'success')
    },
    onError: () => showToast('Failed to complete', 'error'),
  })

  const scoreMut = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: any }) => scoreInterview(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['institution-interviews'] })
      showToast('Interview scored', 'success')
      setShowScoreModal(false)
    },
    onError: () => showToast('Failed to score', 'error'),
  })

  const columns = [
    { key: 'application_id', label: 'Student', render: (row: Interview) => row.application_id.slice(0, 10) + '...' },
    { key: 'interview_type', label: 'Type', render: (row: Interview) => <Badge variant="info">{row.interview_type}</Badge> },
    { key: 'confirmed_time', label: 'Date', render: (row: Interview) => formatDateTime(row.confirmed_time ?? row.proposed_times[0]) },
    { key: 'status', label: 'Status', render: (row: Interview) => <Badge variant={(STATUS_COLORS[row.status] as any) ?? 'neutral'}>{row.status}</Badge> },
    { key: 'duration_minutes', label: 'Duration', render: (row: Interview) => `${row.duration_minutes} min` },
    {
      key: 'actions',
      label: '',
      render: (row: Interview) => (
        <div className="flex gap-1">
          {row.status === 'confirmed' && (
            <Button size="sm" variant="ghost" onClick={() => completeMut.mutate(row.id)}>Complete</Button>
          )}
          {row.status === 'completed' && (
            <Button size="sm" variant="ghost" onClick={() => { setSelectedInterview(row.id); setShowScoreModal(true) }}>Score</Button>
          )}
        </div>
      ),
    },
  ]

  const addTime = () => setSchedTimes([...schedTimes, ''])
  const removeTime = (i: number) => setSchedTimes(schedTimes.filter((_, idx) => idx !== i))
  const updateTime = (i: number, v: string) => setSchedTimes(schedTimes.map((t, idx) => idx === i ? v : t))

  const handleSchedule = () => {
    if (!schedAppId) { showToast('Select an application', 'warning'); return }
    const validTimes = schedTimes.filter(Boolean)
    if (validTimes.length === 0) { showToast('Add at least one proposed time', 'warning'); return }
    proposeMut.mutate({
      application_id: schedAppId,
      interviewer_id: '', // filled by backend
      interview_type: schedType,
      proposed_times: validTimes,
      duration_minutes: Number(schedDuration),
      location_or_link: schedLocation || null,
    })
  }

  return (
    <div className="p-6 space-y-4">
      <InstitutionPageHeader
        title="Interviews"
        description="Coordinate scheduling, interview completion, and interviewer recommendations."
        actions={(
          <Button onClick={() => setShowScheduleModal(true)} className="flex items-center gap-2">
            <Plus size={16} /> Schedule Interview
          </Button>
        )}
      />

      {interviews.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <Card className="p-3">
            <p className="text-xs text-gray-500">Confirmed</p>
            <p className="text-xl font-semibold text-brand-slate-700">{confirmedCount}</p>
          </Card>
          <Card className="p-3">
            <p className="text-xs text-gray-500">Proposed</p>
            <p className="text-xl font-semibold text-amber-700">{proposedCount}</p>
          </Card>
          <Card className="p-3">
            <p className="text-xs text-gray-500">Completed</p>
            <p className="text-xl font-semibold text-emerald-700">{completedCount}</p>
          </Card>
        </div>
      )}

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      <Card>
        {interviewsQ.isLoading ? (
          <div className="p-4 space-y-2">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-12" />)}</div>
        ) : filteredInterviews.length === 0 ? (
          <EmptyState
            icon={<Calendar size={40} />}
            title="No interviews"
            description="Schedule interviews from the pipeline or by clicking the button above."
          />
        ) : (
          <div className="overflow-x-auto">
            <Table columns={columns} data={filteredInterviews} />
          </div>
        )}
      </Card>

      {/* Schedule Modal */}
      <Modal isOpen={showScheduleModal} onClose={() => setShowScheduleModal(false)} title="Schedule Interview">
        <div className="space-y-4">
          <Input label="Application ID" value={schedAppId} onChange={e => setSchedAppId(e.target.value)} placeholder="Paste application ID" />
          <Select label="Interview Type" options={INTERVIEW_TYPES} value={schedType} onChange={e => setSchedType(e.target.value)} />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Proposed Times</label>
            {schedTimes.map((t, i) => (
              <div key={i} className="flex items-center gap-2 mb-2">
                <Input type="datetime-local" value={t} onChange={e => updateTime(i, e.target.value)} className="flex-1" />
                {schedTimes.length > 1 && (
                  <button onClick={() => removeTime(i)} className="p-1 text-gray-400 hover:text-red-500"><Trash2 size={16} /></button>
                )}
              </div>
            ))}
            <Button variant="ghost" size="sm" onClick={addTime} className="flex items-center gap-1">
              <Plus size={14} /> Add Time
            </Button>
          </div>
          <Input label="Duration (minutes)" type="number" value={schedDuration} onChange={e => setSchedDuration(e.target.value)} />
          <Input label="Location / Link" value={schedLocation} onChange={e => setSchedLocation(e.target.value)} placeholder="Zoom link or address" />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setShowScheduleModal(false)}>Cancel</Button>
            <Button onClick={handleSchedule} disabled={proposeMut.isPending}>
              {proposeMut.isPending ? 'Scheduling...' : 'Schedule'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Score Modal */}
      <Modal isOpen={showScoreModal} onClose={() => setShowScoreModal(false)} title="Score Interview">
        <div className="space-y-4">
          <Textarea label="Notes" value={scoreNotes} onChange={e => setScoreNotes(e.target.value)} rows={3} />
          <Select
            label="Recommendation"
            options={[
              { value: 'strong_admit', label: 'Strong Admit' },
              { value: 'admit', label: 'Admit' },
              { value: 'borderline', label: 'Borderline' },
              { value: 'reject', label: 'Reject' },
            ]}
            value={scoreRec}
            onChange={e => setScoreRec(e.target.value)}
            placeholder="Select recommendation"
          />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setShowScoreModal(false)}>Cancel</Button>
            <Button
              onClick={() => {
                if (!selectedInterview) return
                scoreMut.mutate({
                  id: selectedInterview,
                  payload: {
                    criterion_scores: scoreCriteria,
                    total_weighted_score: 0,
                    interviewer_notes: scoreNotes || null,
                    recommendation: scoreRec || null,
                  },
                })
              }}
              disabled={scoreMut.isPending}
            >
              {scoreMut.isPending ? 'Saving...' : 'Submit Score'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
