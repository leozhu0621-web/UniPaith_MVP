import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { CalendarRange, Plus, Edit2, Trash2, Users, CheckCircle2 } from 'lucide-react'
import {
  getIntakeRounds, createIntakeRound, updateIntakeRound, deleteIntakeRound,
  getInstitutionPrograms,
} from '../../api/institutions'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import Input from '../../components/ui/Input'
import Select from '../../components/ui/Select'
import EmptyState from '../../components/ui/EmptyState'
import Skeleton from '../../components/ui/Skeleton'
import InstitutionPageHeader from '../../components/institution/InstitutionPageHeader'
import { showToast } from '../../stores/toast-store'
import { formatDate } from '../../utils/format'
import type { IntakeRound, Program } from '../../types'

const STATUS_BADGE: Record<string, 'info' | 'success' | 'neutral' | 'warning'> = {
  upcoming: 'info',
  open: 'success',
  closed: 'warning',
  completed: 'neutral',
}

export default function IntakeRoundsPage() {
  const queryClient = useQueryClient()
  const [selectedProgram, setSelectedProgram] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editTarget, setEditTarget] = useState<IntakeRound | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<IntakeRound | null>(null)

  // Form
  const [roundName, setRoundName] = useState('')
  const [intakeTerm, setIntakeTerm] = useState('')
  const [appOpen, setAppOpen] = useState('')
  const [appDeadline, setAppDeadline] = useState('')
  const [decisionDate, setDecisionDate] = useState('')
  const [progStart, setProgStart] = useState('')
  const [capacity, setCapacity] = useState('')
  const [sortOrder, setSortOrder] = useState('0')

  const programsQ = useQuery({ queryKey: ['institution-programs'], queryFn: getInstitutionPrograms })
  const programs: Program[] = Array.isArray(programsQ.data) ? programsQ.data : []
  const programOptions = [{ value: '', label: 'Select Program...' }, ...programs.map(p => ({ value: p.id, label: p.program_name }))]

  const intakesQ = useQuery({
    queryKey: ['intake-rounds', selectedProgram],
    queryFn: () => getIntakeRounds(selectedProgram),
    enabled: !!selectedProgram,
  })
  const intakes: IntakeRound[] = Array.isArray(intakesQ.data) ? intakesQ.data : []

  const resetForm = () => {
    setRoundName(''); setIntakeTerm(''); setAppOpen(''); setAppDeadline('')
    setDecisionDate(''); setProgStart(''); setCapacity(''); setSortOrder('0'); setEditTarget(null)
  }
  const openCreate = () => { resetForm(); setShowModal(true) }
  const openEdit = (r: IntakeRound) => {
    setEditTarget(r); setRoundName(r.round_name); setIntakeTerm(r.intake_term || '')
    setAppOpen(r.application_open || ''); setAppDeadline(r.application_deadline || '')
    setDecisionDate(r.decision_date || ''); setProgStart(r.program_start || '')
    setCapacity(r.capacity?.toString() || ''); setSortOrder(r.sort_order.toString())
    setShowModal(true)
  }

  const createMut = useMutation({
    mutationFn: (p: Parameters<typeof createIntakeRound>[1]) => createIntakeRound(selectedProgram, p),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['intake-rounds'] }); setShowModal(false); resetForm(); showToast('Intake round created', 'success') },
  })
  const updateMut = useMutation({
    mutationFn: (p: { id: string; payload: Parameters<typeof updateIntakeRound>[2] }) => updateIntakeRound(selectedProgram, p.id, p.payload),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['intake-rounds'] }); setShowModal(false); resetForm(); showToast('Intake round updated', 'success') },
  })
  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteIntakeRound(selectedProgram, id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['intake-rounds'] }); setDeleteTarget(null); showToast('Intake round deleted', 'success') },
  })
  const statusMut = useMutation({
    mutationFn: (p: { id: string; status: string }) => updateIntakeRound(selectedProgram, p.id, { status: p.status }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['intake-rounds'] }); showToast('Status updated', 'success') },
  })

  const handleSubmit = () => {
    if (!roundName.trim()) { showToast('Round name is required', 'warning'); return }
    const payload = {
      round_name: roundName,
      intake_term: intakeTerm || undefined,
      application_open: appOpen || undefined,
      application_deadline: appDeadline || undefined,
      decision_date: decisionDate || undefined,
      program_start: progStart || undefined,
      capacity: capacity ? parseInt(capacity) : undefined,
      sort_order: parseInt(sortOrder) || 0,
    }
    if (editTarget) updateMut.mutate({ id: editTarget.id, payload })
    else createMut.mutate(payload)
  }

  return (
    <div className="p-6 space-y-4">
      <InstitutionPageHeader
        title="Intake Rounds"
        description="Configure multiple intake windows per program with separate deadlines, capacity, and requirements."
        actions={selectedProgram ? <Button onClick={openCreate} className="flex items-center gap-2"><Plus size={16} /> New Round</Button> : undefined}
      />

      <Card className="p-4">
        <Select label="Program" options={programOptions} value={selectedProgram} onChange={e => setSelectedProgram(e.target.value)} />
      </Card>

      {!selectedProgram ? (
        <EmptyState icon={<CalendarRange size={40} />} title="Select a program" description="Choose a program to manage its intake rounds." />
      ) : intakesQ.isLoading ? (
        <div className="space-y-3">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-32" />)}</div>
      ) : intakes.length === 0 ? (
        <EmptyState icon={<CalendarRange size={40} />} title="No intake rounds" description="Create intake rounds with deadlines, capacity limits, and requirement sets." action={{ label: 'New Round', onClick: openCreate }} />
      ) : (
        <div className="space-y-3">
          {intakes.map(r => (
            <Card key={r.id} className="p-4">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-gray-900">{r.round_name}</h3>
                    <Badge variant={STATUS_BADGE[r.status] ?? 'neutral'}>{r.status}</Badge>
                    {r.intake_term && <Badge variant="info">{r.intake_term}</Badge>}
                    {!r.is_active && <Badge variant="neutral">Inactive</Badge>}
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm mb-3">
                {r.application_open && (
                  <div><span className="text-gray-400 text-xs">Opens</span><p className="text-gray-700">{formatDate(r.application_open)}</p></div>
                )}
                {r.application_deadline && (
                  <div><span className="text-gray-400 text-xs">Deadline</span><p className="text-gray-700 font-medium">{formatDate(r.application_deadline)}</p></div>
                )}
                {r.decision_date && (
                  <div><span className="text-gray-400 text-xs">Decision</span><p className="text-gray-700">{formatDate(r.decision_date)}</p></div>
                )}
                {r.program_start && (
                  <div><span className="text-gray-400 text-xs">Starts</span><p className="text-gray-700">{formatDate(r.program_start)}</p></div>
                )}
              </div>
              {r.capacity != null && (
                <div className="flex items-center gap-2 text-sm mb-2">
                  <Users size={14} className="text-gray-400" />
                  <span className="text-gray-600">{r.enrolled_count} / {r.capacity} enrolled</span>
                  {r.spots_remaining != null && (
                    <Badge variant={r.spots_remaining > 0 ? 'success' : 'warning'}>
                      {r.spots_remaining > 0 ? `${r.spots_remaining} spots left` : 'Full'}
                    </Badge>
                  )}
                </div>
              )}
              <div className="flex gap-2 mt-2">
                <Button variant="ghost" size="sm" onClick={() => openEdit(r)} className="flex items-center gap-1"><Edit2 size={14} /> Edit</Button>
                {r.status === 'upcoming' && (
                  <Button variant="ghost" size="sm" onClick={() => statusMut.mutate({ id: r.id, status: 'open' })} className="flex items-center gap-1 text-green-600"><CheckCircle2 size={14} /> Open</Button>
                )}
                {r.status === 'open' && (
                  <Button variant="ghost" size="sm" onClick={() => statusMut.mutate({ id: r.id, status: 'closed' })} className="flex items-center gap-1 text-amber-600">Close</Button>
                )}
                <Button variant="ghost" size="sm" onClick={() => setDeleteTarget(r)} className="flex items-center gap-1 text-red-600"><Trash2 size={14} /></Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create/Edit Modal */}
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); resetForm() }} title={editTarget ? 'Edit Intake Round' : 'New Intake Round'}>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <Input label="Round Name *" value={roundName} onChange={e => setRoundName(e.target.value)} placeholder="e.g. Round 1, Early Action" />
            <Input label="Term" value={intakeTerm} onChange={e => setIntakeTerm(e.target.value)} placeholder="e.g. Fall 2026" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Input label="Application Opens" type="date" value={appOpen} onChange={e => setAppOpen(e.target.value)} />
            <Input label="Application Deadline" type="date" value={appDeadline} onChange={e => setAppDeadline(e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Input label="Decision Date" type="date" value={decisionDate} onChange={e => setDecisionDate(e.target.value)} />
            <Input label="Program Start" type="date" value={progStart} onChange={e => setProgStart(e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Input label="Capacity" type="number" value={capacity} onChange={e => setCapacity(e.target.value)} placeholder="Max students" />
            <Input label="Sort Order" type="number" value={sortOrder} onChange={e => setSortOrder(e.target.value)} />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => { setShowModal(false); resetForm() }}>Cancel</Button>
            <Button onClick={handleSubmit} disabled={createMut.isPending || updateMut.isPending}>
              {(createMut.isPending || updateMut.isPending) ? 'Saving...' : 'Save'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Modal */}
      <Modal isOpen={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="Delete Intake Round">
        <p className="text-sm text-gray-600 mb-4">Delete <strong>{deleteTarget?.round_name}</strong>?</p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button variant="danger" onClick={() => deleteTarget && deleteMut.mutate(deleteTarget.id)} disabled={deleteMut.isPending}>
            {deleteMut.isPending ? 'Deleting...' : 'Delete'}
          </Button>
        </div>
      </Modal>
    </div>
  )
}
