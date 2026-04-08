import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, MoreVertical, Edit2, Eye, EyeOff, Trash2, BookOpen } from 'lucide-react'
import { getInstitutionPrograms, publishProgram, unpublishProgram, deleteProgram } from '../../api/institutions'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Table from '../../components/ui/Table'
import Dropdown from '../../components/ui/Dropdown'
import EmptyState from '../../components/ui/EmptyState'
import Modal from '../../components/ui/Modal'
import InstitutionPageHeader from '../../components/institution/InstitutionPageHeader'
import { showToast } from '../../stores/toast-store'
import { formatDate, formatCurrency } from '../../utils/format'
import { DEGREE_LABELS } from '../../utils/constants'
import type { Program } from '../../types'

export default function ProgramsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [deleteTarget, setDeleteTarget] = useState<Program | null>(null)

  const programsQ = useQuery({ queryKey: ['institution-programs'], queryFn: getInstitutionPrograms })
  const programs: Program[] = Array.isArray(programsQ.data) ? programsQ.data : []

  const publishMut = useMutation({
    mutationFn: publishProgram,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['institution-programs'] })
      showToast('Program published', 'success')
    },
    onError: () => showToast('Failed to publish', 'error'),
  })

  const unpublishMut = useMutation({
    mutationFn: unpublishProgram,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['institution-programs'] })
      showToast('Program unpublished', 'success')
    },
    onError: () => showToast('Failed to unpublish', 'error'),
  })

  const deleteMut = useMutation({
    mutationFn: deleteProgram,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['institution-programs'] })
      showToast('Program deleted', 'success')
      setDeleteTarget(null)
    },
    onError: () => showToast('Failed to delete', 'error'),
  })

  const columns = [
    {
      key: 'program_name',
      label: 'Name',
      render: (row: Program) => (
        <button onClick={() => navigate(`/i/programs/${row.id}/edit`)} className="text-brand-slate-600 hover:underline font-medium">
          {row.program_name}
        </button>
      ),
    },
    {
      key: 'degree_type',
      label: 'Degree',
      render: (row: Program) => <Badge variant="info">{DEGREE_LABELS[row.degree_type] ?? row.degree_type}</Badge>,
    },
    {
      key: 'is_published',
      label: 'Status',
      render: (row: Program) => (
        <Badge variant={row.is_published ? 'success' : 'neutral'}>
          {row.is_published ? 'Published' : 'Draft'}
        </Badge>
      ),
    },
    {
      key: 'application_deadline',
      label: 'Deadline',
      render: (row: Program) => formatDate(row.application_deadline),
    },
    {
      key: 'tuition',
      label: 'Tuition',
      render: (row: Program) => formatCurrency(row.tuition),
    },
    {
      key: 'actions',
      label: '',
      render: (row: Program) => (
        <Dropdown
          trigger={<button className="p-1 rounded hover:bg-gray-100"><MoreVertical size={16} className="text-gray-500" /></button>}
          items={[
            { label: 'Edit', icon: <Edit2 size={14} />, onClick: () => navigate(`/i/programs/${row.id}/edit`) },
            row.is_published
              ? { label: 'Unpublish', icon: <EyeOff size={14} />, onClick: () => unpublishMut.mutate(row.id) }
              : { label: 'Publish', icon: <Eye size={14} />, onClick: () => publishMut.mutate(row.id) },
            { label: 'Delete', icon: <Trash2 size={14} />, onClick: () => setDeleteTarget(row), variant: 'danger' as const },
          ]}
        />
      ),
    },
  ]

  return (
    <div className="p-6 space-y-4">
      <InstitutionPageHeader
        title="Programs"
        description="Manage catalog readiness, publication status, and admissions deadlines."
        actions={(
          <Button onClick={() => navigate('/i/programs/new')} className="flex items-center gap-2">
            <Plus size={16} /> New Program
          </Button>
        )}
      />

      {programs.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <Card className="p-3">
            <p className="text-xs text-gray-500">Total Programs</p>
            <p className="text-xl font-semibold text-gray-900">{programs.length}</p>
          </Card>
          <Card className="p-3">
            <p className="text-xs text-gray-500">Published</p>
            <p className="text-xl font-semibold text-emerald-700">{programs.filter(p => p.is_published).length}</p>
          </Card>
          <Card className="p-3">
            <p className="text-xs text-gray-500">Drafts to Publish</p>
            <p className="text-xl font-semibold text-amber-700">{programs.filter(p => !p.is_published).length}</p>
          </Card>
        </div>
      )}

      <Card>
        {programs.length === 0 && !programsQ.isLoading ? (
          <EmptyState
            icon={<BookOpen size={40} />}
            title="No programs yet"
            description="Create your first program to start accepting applications."
            action={{ label: 'New Program', onClick: () => navigate('/i/programs/new') }}
          />
        ) : (
          <div className="overflow-x-auto">
            <Table columns={columns} data={programs} isLoading={programsQ.isLoading} />
          </div>
        )}
      </Card>

      {/* Delete Confirmation */}
      <Modal isOpen={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="Delete Program">
        <p className="text-sm text-gray-600 mb-4">
          Are you sure you want to delete <strong>{deleteTarget?.program_name}</strong>? This action cannot be undone.
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button
            variant="danger"
            onClick={() => deleteTarget && deleteMut.mutate(deleteTarget.id)}
            disabled={deleteMut.isPending}
          >
            {deleteMut.isPending ? 'Deleting...' : 'Delete'}
          </Button>
        </div>
      </Modal>
    </div>
  )
}
