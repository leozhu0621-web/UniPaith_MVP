import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ClipboardList, Plus, Edit2, Trash2, GripVertical } from 'lucide-react'
import {
  DndContext, type DragEndEvent, KeyboardSensor, PointerSensor,
  closestCenter, useSensor, useSensors,
} from '@dnd-kit/core'
import {
  SortableContext, arrayMove, useSortable, verticalListSortingStrategy,
  sortableKeyboardCoordinates,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import {
  getProgramChecklist, createChecklistItem, updateChecklistItem, deleteChecklistItem,
  reorderChecklistItems, getInstitutionPrograms,
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
import QueryError from '../../components/ui/QueryError'
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

// Sortable row wrapper — Spec 47 G-I3.
function SortableChecklistItem({
  item, onEdit, onDelete,
}: {
  item: ProgramChecklistItem
  onEdit: (i: ProgramChecklistItem) => void
  onDelete: (i: ProgramChecklistItem) => void
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: item.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : undefined,
    zIndex: isDragging ? 10 : undefined,
  } as React.CSSProperties

  return (
    <div ref={setNodeRef} style={style}>
      <Card pad={false} className={`p-3 flex items-center gap-3 ${!item.is_active ? 'opacity-50' : ''}`}>
      <button
        type="button"
        aria-label={`Reorder ${item.item_name}`}
        className="ui-btn touch-target -ml-1 px-1 py-1 rounded-md text-muted-foreground hover:bg-muted hover:text-foreground transition-colors cursor-grab active:cursor-grabbing focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        {...attributes}
        {...listeners}
      >
        <GripVertical size={16} />
      </button>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5 flex-wrap">
          <span className="text-sm font-semibold text-foreground">{item.item_name}</span>
          <Badge variant={LEVEL_BADGE[item.requirement_level] ?? 'neutral'}>
            {item.requirement_level.replace('_', ' ')}
          </Badge>
          <Badge variant="neutral">{CATEGORY_ICON[item.category] ?? item.category}</Badge>
          {!item.is_active && <Badge variant="neutral">Inactive</Badge>}
        </div>
        {item.description && (
          <p className="text-xs text-muted-foreground truncate">{item.description}</p>
        )}
      </div>
      <div className="flex gap-1 shrink-0">
        <Button variant="ghost" size="sm" onClick={() => onEdit(item)} aria-label="Edit">
          <Edit2 size={14} />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onDelete(item)}
          className="text-destructive hover:text-destructive"
          aria-label="Delete"
        >
          <Trash2 size={14} />
        </Button>
      </div>
      </Card>
    </div>
  )
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
  // Sort by sort_order so drag reflects persisted order.
  const orderedItems = [...items].sort((a, b) => a.sort_order - b.sort_order)

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
    onError: () => showToast("We couldn't add the item. Please try again.", 'error'),
  })
  const updateMut = useMutation({
    mutationFn: (p: { id: string; payload: Parameters<typeof updateChecklistItem>[2] }) => updateChecklistItem(selectedProgram, p.id, p.payload),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['program-checklist'] }); setShowModal(false); resetForm(); showToast('Item updated', 'success') },
    onError: () => showToast("We couldn't update the item. Please try again.", 'error'),
  })
  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteChecklistItem(selectedProgram, id),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['program-checklist'] }); setDeleteTarget(null); showToast('Item removed', 'success') },
    onError: () => showToast("We couldn't remove the item. Please try again.", 'error'),
  })

  // Reorder mutation — optimistic so drag feels instant.
  const reorderMut = useMutation({
    mutationFn: (orderedIds: string[]) =>
      reorderChecklistItems(selectedProgram, orderedIds, orderedItems),
    onMutate: async (orderedIds: string[]) => {
      await queryClient.cancelQueries({ queryKey: ['program-checklist', selectedProgram] })
      const previous = queryClient.getQueryData<ProgramChecklistItem[]>(
        ['program-checklist', selectedProgram],
      )
      if (previous) {
        const map = new Map(previous.map(it => [it.id, it]))
        const next = orderedIds
          .map((id, index) => {
            const it = map.get(id)
            return it ? { ...it, sort_order: index * 10 } : null
          })
          .filter(Boolean) as ProgramChecklistItem[]
        queryClient.setQueryData<ProgramChecklistItem[]>(
          ['program-checklist', selectedProgram],
          next,
        )
      }
      return { previous }
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(
          ['program-checklist', selectedProgram],
          context.previous,
        )
      }
      showToast('Reorder failed — restored previous order', 'error')
    },
    onSuccess: () => {
      showToast('Order saved', 'success')
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['program-checklist', selectedProgram] })
    },
  })

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  const onDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    if (!over || active.id === over.id) return
    const oldIndex = orderedItems.findIndex(i => i.id === active.id)
    const newIndex = orderedItems.findIndex(i => i.id === over.id)
    if (oldIndex < 0 || newIndex < 0) return
    const newOrderIds = arrayMove(orderedItems, oldIndex, newIndex).map(i => i.id)
    reorderMut.mutate(newOrderIds)
  }

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

  const requiredItems = orderedItems.filter(i => i.requirement_level === 'required' && i.is_active)
  const optionalItems = orderedItems.filter(i => i.requirement_level === 'optional' && i.is_active)
  const otherItems = orderedItems.filter(i => !['required', 'optional'].includes(i.requirement_level) || !i.is_active)

  return (
    <div className="p-6 space-y-4">
      <InstitutionPageHeader
        title="Requirements Checklist"
        actions={selectedProgram ? <Button onClick={openCreate} className="flex items-center gap-2"><Plus size={16} /> Add Item</Button> : undefined}
      />

      <Card pad={false} className="p-4">
        <Select label="Program" options={programOptions} value={selectedProgram} onChange={e => setSelectedProgram(e.target.value)} />
      </Card>

      {!selectedProgram ? (
        <EmptyState icon={<ClipboardList size={40} />} title="Select a program" />
      ) : checklistQ.isLoading ? (
        <Skeleton className="h-60" />
      ) : checklistQ.isError ? (
        <QueryError detail="We couldn't load this program's checklist." onRetry={() => checklistQ.refetch()} />
      ) : orderedItems.length === 0 ? (
        <EmptyState icon={<ClipboardList size={40} />} title="No checklist items" action={{ label: 'Add Item', onClick: openCreate }} />
      ) : (
        <div className="space-y-4">
          {/* Summary */}
          <div className="grid grid-cols-3 gap-3">
            <Card pad={false} className="p-3 border-warning-soft">
              <p className="text-xs text-warning">Required</p>
              <p className="text-xl font-bold text-warning">{requiredItems.length}</p>
            </Card>
            <Card pad={false} className="p-3 border-secondary/30">
              <p className="text-xs text-secondary">Optional</p>
              <p className="text-xl font-bold text-secondary">{optionalItems.length}</p>
            </Card>
            <Card pad={false} className="p-3">
              <p className="text-xs text-muted-foreground">Other</p>
              <p className="text-xl font-semibold text-foreground">{otherItems.length}</p>
            </Card>
          </div>

          {/* Items list — drag to reorder */}
          <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={onDragEnd}>
            <SortableContext items={orderedItems.map(i => i.id)} strategy={verticalListSortingStrategy}>
              <div className="space-y-2">
                {orderedItems.map(item => (
                  <SortableChecklistItem
                    key={item.id}
                    item={item}
                    onEdit={openEdit}
                    onDelete={setDeleteTarget}
                  />
                ))}
              </div>
            </SortableContext>
          </DndContext>
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
          <Input label="Sort Order" type="number" value={sortOrder} onChange={e => setSortOrder(e.target.value)} helperText="Drag items in the list to reorder visually; this number is the raw value." />
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
        <p className="text-sm text-muted-foreground mb-4">Remove <strong className="text-foreground">{deleteTarget?.item_name}</strong> from this program's checklist?</p>
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
