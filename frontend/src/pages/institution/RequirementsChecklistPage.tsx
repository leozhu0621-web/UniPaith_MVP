import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ClipboardList, Plus, Edit2, Trash2, GripVertical } from 'lucide-react'
import {
  getProgramChecklist, createChecklistItem, updateChecklistItem, deleteChecklistItem,
  getInstitutionPrograms,
} from '../../api/institutions'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import Input from '../../components/ui/Input'
import Select from '../../components/ui/Select'
import Textarea from '../../components/ui/Textarea'
import EmptyState from '../../components/ui/EmptyState'
import Skeleton from '../../components/ui/Skeleton'
import InstitutionPageHeader from '../../components/institution/InstitutionPageHeader'
import { showToast } from '../../stores/toast-store'
import type { ProgramChecklistItem, Program } from '../../types'

const CATEGORY_OPTIONS = [
  { value: 'essay', label: 'Essay' },
  { value: 'test_score', label: 'Test Score' },
  { value: 'recommendation', label: 'Recommendation' },
  { value: 'interview', label: 'Interview' },
  { value: 'portfolio', label: 'Portfolio' },
  { value: 'document', label: 'Document' },
  { value: 'financial', label: 'Financial' },
  { value: 'other', label: 'Other' },
]

const LEVEL_OPTIONS = [
  { value: 'required', label: 'Required' },
  { value: 'optional', label: 'Optional' },
  { value: 'conditional', label: 'Conditional' },
  { value: 'not_applicable', label: 'N/A' },
]

const LEVEL_BADGE: Record<string, 'warning' | 'info' | 'neutral' | 'success'> = {
  required: 'warning',
  optional: 'info',
  conditional: 'neutral',
  not_applicable: 'neutral',
}

const CATEGORY_ICON: Record<string, string> = {
  essay: 'Essay', test_score: 'Test', recommendation: 'Rec',
  interview: 'Interview', portfolio: 'Portfolio', document: 'Doc',
  financial: 'Financial', other: 'Other',
}

export default function RequirementsChecklistPage() {
  const queryClient = useQueryClient()
  const [selectedProgram, setSelectedProgram] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editTarget, setEditTarget] = useState<ProgramChecklistItem | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<ProgramChecklistItem | null>(null)

  const [itemName, setItemName] = useState('')
  const [category, setCategory] = useState('document')
  const [level, setLevel] = useState('required')
  const [description, setDescription] = useState('')
  const [instructions, setInstructions] = useState('')
  const [sortOrder, setSortOrder] = useState('0')

  const programsQ = useQuery({ queryKey: ['institution-programs'], queryFn: getInstitutionPrograms })
  const programs: Program[] = Array.isArray(programsQ.data) ? programsQ.data : []
  const programOptions = [{ value: '', label: 'Select Program...' }, ...programs.map(p => ({ value: p.id, label: p.program_name }))]

  const checklistQ = useQuery({
    queryKey: ['program-checklist', selectedProgram],
    queryFn: () => getProgramChecklist(selectedProgram),
    enabled: !!selectedProgram,
  })
  const items: ProgramChecklistItem[] = Array.isArray(checklistQ.data) ? checklistQ.data : []

  const resetForm = () => {
    setItemName(''); setCategory('document'); setLevel('required')
    setDescription(''); setInstructions(''); setSortOrder('0'); setEditTarget(null)
  }
  const openCreate = () => { resetForm(); setShowModal(true) }
  const openEdit = (item: ProgramChecklistItem) => {
    setEditTarget(item); setItemName(item.item_name); setCategory(item.category)
    setLevel(item.requirement_level); setDescription(item.description || '')
    setInstructions(item.instructions || ''); setSortOrder(item.sort_order.toString())
    setShowModal(true)
  }

  const createMut = useMutation({
    mutationFn: (p: Parameters<typeof createChecklistItem>[1]) => createChecklistItem(selectedProgram, p),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['program-checklist'] }); setShowModal(false); resetForm(); showToast('Item added', 'success') },
  })
  const updateMut = useMutation({
    mutationFn: (p: { id: string; payload: Parameters<typeof updateChecklistItem>[2] }) => updateChecklistItem(selectedProgram, p.id, p.payload),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['program-checklist'] }); setShowModal(false); resetForm(); showToast('Item updated', 'success') },
  })
  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteChecklistItem(selectedProgram, id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['program-checklist'] }); setDeleteTarget(null); showToast('Item removed', 'success') },
  })

  const handleSubmit = () => {
    if (!itemName.trim()) { showToast('Item name is required', 'warning'); return }
    const payload = {
      item_name: itemName, category, requirement_level: level,
      description: description || undefined, instructions: instructions || undefined,
      sort_order: parseInt(sortOrder) || 0,
    }
    if (editTarget) updateMut.mutate({ id: editTarget.id, payload })
    else createMut.mutate(payload)
  }

  const requiredItems = items.filter(i => i.requirement_level === 'required' && i.is_active)
  const optionalItems = items.filter(i => i.requirement_level === 'optional' && i.is_active)
  const otherItems = items.filter(i => !['required', 'optional'].includes(i.requirement_level) || !i.is_active)

  return (
    <div className="p-6 space-y-4">
      <InstitutionPageHeader
        title="Requirements Checklist"
        description="Configure per-program requirements: what's required, optional, conditional, or N/A."
        actions={selectedProgram ? <Button onClick={openCreate} className="flex items-center gap-2"><Plus size={16} /> Add Item</Button> : undefined}
      />

      <Card className="p-4">
        <Select label="Program" options={programOptions} value={selectedProgram} onChange={e => setSelectedProgram(e.target.value)} />
      </Card>

      {!selectedProgram ? (
        <EmptyState icon={<ClipboardList size={40} />} title="Select a program" description="Choose a program to configure its application requirements checklist." />
      ) : checklistQ.isLoading ? (
        <Skeleton className="h-60" />
      ) : items.length === 0 ? (
        <EmptyState icon={<ClipboardList size={40} />} title="No checklist items" description="Add required and optional items applicants need to submit." action={{ label: 'Add Item', onClick: openCreate }} />
      ) : (
        <div className="space-y-4">
          {/* Summary */}
          <div className="grid grid-cols-3 gap-3">
            <Card className="p-3 border-amber-200">
              <p className="text-xs text-amber-600">Required</p>
              <p className="text-xl font-bold text-amber-700">{requiredItems.length}</p>
            </Card>
            <Card className="p-3 border-blue-200">
              <p className="text-xs text-blue-600">Optional</p>
              <p className="text-xl font-bold text-blue-700">{optionalItems.length}</p>
            </Card>
            <Card className="p-3">
              <p className="text-xs text-gray-500">Other</p>
              <p className="text-xl font-semibold text-gray-700">{otherItems.length}</p>
            </Card>
          </div>

          {/* Items list */}
          <div className="space-y-2">
            {items.map(item => (
              <Card key={item.id} className={`p-3 flex items-center gap-3 ${!item.is_active ? 'opacity-50' : ''}`}>
                <GripVertical size={14} className="text-gray-300 shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-sm font-medium text-gray-900">{item.item_name}</span>
                    <Badge variant={LEVEL_BADGE[item.requirement_level] ?? 'neutral'}>{item.requirement_level.replace('_', ' ')}</Badge>
                    <Badge variant="neutral">{CATEGORY_ICON[item.category] ?? item.category}</Badge>
                    {!item.is_active && <Badge variant="neutral">Inactive</Badge>}
                  </div>
                  {item.description && <p className="text-xs text-gray-500 truncate">{item.description}</p>}
                </div>
                <div className="flex gap-1 shrink-0">
                  <Button variant="ghost" size="sm" onClick={() => openEdit(item)}><Edit2 size={14} /></Button>
                  <Button variant="ghost" size="sm" onClick={() => setDeleteTarget(item)} className="text-red-500"><Trash2 size={14} /></Button>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Create/Edit Modal */}
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); resetForm() }} title={editTarget ? 'Edit Requirement' : 'Add Requirement'}>
        <div className="space-y-4">
          <Input label="Item Name *" value={itemName} onChange={e => setItemName(e.target.value)} placeholder="e.g. Statement of Purpose, GRE Scores" />
          <div className="grid grid-cols-2 gap-3">
            <Select label="Category" options={CATEGORY_OPTIONS} value={category} onChange={e => setCategory(e.target.value)} />
            <Select label="Requirement Level" options={LEVEL_OPTIONS} value={level} onChange={e => setLevel(e.target.value)} />
          </div>
          <Textarea label="Description" value={description} onChange={e => setDescription(e.target.value)} rows={2} placeholder="What this requirement is about..." />
          <Textarea label="Instructions for Applicants" value={instructions} onChange={e => setInstructions(e.target.value)} rows={2} placeholder="Specific instructions on how to fulfill this requirement..." />
          <Input label="Sort Order" type="number" value={sortOrder} onChange={e => setSortOrder(e.target.value)} />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => { setShowModal(false); resetForm() }}>Cancel</Button>
            <Button onClick={handleSubmit} disabled={createMut.isPending || updateMut.isPending}>
              {(createMut.isPending || updateMut.isPending) ? 'Saving...' : 'Save'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Modal */}
      <Modal isOpen={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="Remove Requirement">
        <p className="text-sm text-gray-600 mb-4">Remove <strong>{deleteTarget?.item_name}</strong> from this program's checklist?</p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button variant="danger" onClick={() => deleteTarget && deleteMut.mutate(deleteTarget.id)} disabled={deleteMut.isPending}>
            {deleteMut.isPending ? 'Removing...' : 'Remove'}
          </Button>
        </div>
      </Modal>
    </div>
  )
}
