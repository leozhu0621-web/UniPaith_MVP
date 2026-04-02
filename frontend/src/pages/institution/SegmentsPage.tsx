import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Layers, Plus, Edit2, Trash2, ToggleLeft, ToggleRight } from 'lucide-react'
import { getSegments, createSegment, updateSegment, deleteSegment, getInstitutionPrograms } from '../../api/institutions'
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

const SEGMENT_TEMPLATES = [
  {
    value: '',
    label: 'Custom segment',
    criteria: {},
  },
  {
    value: 'high_match',
    label: 'High match score (80+)',
    criteria: { min_match_score: 80 },
  },
  {
    value: 'under_review',
    label: 'Applications under review',
    criteria: { statuses: ['submitted', 'under_review'] },
  },
  {
    value: 'interview_ready',
    label: 'Interview stage candidates',
    criteria: { statuses: ['interview'] },
  },
]

export default function SegmentsPage() {
  const queryClient = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [editId, setEditId] = useState<string | null>(null)
  const [name, setName] = useState('')
  const [programId, setProgramId] = useState('')
  const [criteriaText, setCriteriaText] = useState('{}')
  const [templateKey, setTemplateKey] = useState('')
  const [isActive, setIsActive] = useState(true)

  const segmentsQ = useQuery({ queryKey: ['segments'], queryFn: getSegments })
  const segments: Segment[] = Array.isArray(segmentsQ.data) ? segmentsQ.data : []

  const programsQ = useQuery({ queryKey: ['institution-programs'], queryFn: getInstitutionPrograms })
  const programs: Program[] = Array.isArray(programsQ.data) ? programsQ.data : []
  const programOptions = [{ value: '', label: 'None' }, ...programs.map(p => ({ value: p.id, label: p.program_name }))]

  const resetForm = () => {
    setEditId(null)
    setName('')
    setProgramId('')
    setCriteriaText('{}')
    setTemplateKey('')
    setIsActive(true)
  }

  const openCreate = () => { resetForm(); setShowModal(true) }
  const openEdit = (seg: Segment) => {
    setEditId(seg.id)
    setName(seg.segment_name)
    setProgramId(seg.program_id ?? '')
    setCriteriaText(JSON.stringify(seg.criteria ?? {}, null, 2))
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
    let criteria: Record<string, any>
    try { criteria = JSON.parse(criteriaText) } catch { showToast('Invalid JSON for criteria', 'error'); return }

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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Recruitment Segments</h1>
          <p className="text-sm text-gray-500 mt-1">Group applicants by shared traits to run targeted outreach.</p>
        </div>
        <Button onClick={openCreate} className="flex items-center gap-2">
          <Plus size={16} /> New Segment
        </Button>
      </div>

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
                <p className="text-xs text-gray-400 mb-3">Created {formatDate(seg.created_at)}</p>
                {seg.criteria && (
                  <pre className="text-xs bg-gray-50 rounded p-2 mb-3 max-h-24 overflow-auto text-gray-600">
                    {JSON.stringify(seg.criteria, null, 2)}
                  </pre>
                )}
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
              if (template) setCriteriaText(JSON.stringify(template.criteria, null, 2))
            }}
          />
          <Textarea
            label="Criteria (JSON)"
            value={criteriaText}
            onChange={e => setCriteriaText(e.target.value)}
            rows={5}
            helperText="Tip: start with a template, then adjust values. Keep this plain JSON object."
          />
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
