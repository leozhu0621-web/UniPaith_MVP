import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Check, Plus, Users } from 'lucide-react'
import {
  createFaculty,
  listFaculty,
  updateFaculty,
  type Faculty,
} from '../../../api/graduate'
import Card from '../../../components/ui/Card'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import Input from '../../../components/ui/Input'
import Select from '../../../components/ui/Select'
import Modal from '../../../components/ui/Modal'
import Skeleton from '../../../components/ui/Skeleton'
import QueryError from '../../../components/ui/QueryError'
import { Toggle } from '../program-editor/widgets'
import { showToast } from '../../../stores/toast-store'
import { TagInput } from './GradWidgets'

interface DeptOption {
  id: string
  name: string
}

function FacultyCard({ faculty }: { faculty: Faculty }) {
  const qc = useQueryClient()
  const [openings, setOpenings] = useState(String(faculty.openings))
  const patch = useMutation({
    mutationFn: (p: Partial<Faculty>) => updateFaculty(faculty.id, p),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['faculty'] }),
    onError: () => showToast('Could not update faculty', 'error'),
  })
  return (
    <div className="rounded-lg border border-border bg-background p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-medium text-foreground">{faculty.name}</span>
            {faculty.title && <span className="text-xs text-muted-foreground">{faculty.title}</span>}
            {faculty.accepting_students ? (
              <Badge variant="success">
                <Check size={11} /> Accepting
              </Badge>
            ) : (
              <Badge variant="neutral">Not accepting</Badge>
            )}
            {faculty.funding_available && <Badge variant="info">Funding</Badge>}
          </div>
          {faculty.research_areas.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {faculty.research_areas.map((a, i) => (
                <span key={i} className="rounded bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                  {a}
                </span>
              ))}
            </div>
          )}
        </div>
        <div className="flex shrink-0 flex-col items-end gap-2">
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-muted-foreground">Openings</span>
            <input
              type="number"
              min={0}
              aria-label={`Openings for ${faculty.name}`}
              value={openings}
              onChange={e => setOpenings(e.target.value)}
              onBlur={() => patch.mutate({ openings: Math.max(0, Number(openings) || 0) })}
              className="w-14 rounded border border-border bg-background px-2 py-1 text-sm tabular-nums text-foreground outline-none focus:border-secondary"
            />
          </div>
          <Toggle
            checked={faculty.accepting_students}
            onChange={v => patch.mutate({ accepting_students: v })}
            label="Accepting students"
          />
          <Toggle
            checked={faculty.funding_available}
            onChange={v => patch.mutate({ funding_available: v })}
            label="Funding available"
          />
        </div>
      </div>
    </div>
  )
}

export default function FacultyRoster({
  departmentId,
  departments,
}: {
  departmentId?: string
  departments: DeptOption[]
}) {
  const qc = useQueryClient()
  const facultyQ = useQuery({
    queryKey: ['faculty', departmentId ?? 'all'],
    queryFn: () => listFaculty(departmentId),
  })
  const [showAdd, setShowAdd] = useState(false)
  const [form, setForm] = useState({
    name: '',
    department_id: departmentId ?? '',
    title: '',
    email: '',
    research_areas: [] as string[],
    accepting_students: true,
    funding_available: false,
    openings: '1',
  })

  const createMut = useMutation({
    mutationFn: () =>
      createFaculty({
        name: form.name.trim(),
        department_id: form.department_id || undefined,
        title: form.title || undefined,
        email: form.email || undefined,
        research_areas: form.research_areas,
        accepting_students: form.accepting_students,
        funding_available: form.funding_available,
        openings: Math.max(0, Number(form.openings) || 0),
      }),
    onSuccess: () => {
      showToast('Faculty added', 'success')
      setShowAdd(false)
      setForm({
        name: '',
        department_id: departmentId ?? '',
        title: '',
        email: '',
        research_areas: [],
        accepting_students: true,
        funding_available: false,
        openings: '1',
      })
      qc.invalidateQueries({ queryKey: ['faculty'] })
    },
    onError: () => showToast('Could not add faculty', 'error'),
  })

  const deptOptions = [
    { value: '', label: '— No department —' },
    ...departments.map(d => ({ value: d.id, label: d.name })),
  ]

  return (
    <Card pad={false} className="p-5">
      <div className="mb-4 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-secondary">
            <Users size={16} />
          </span>
          <h3 className="text-sm font-semibold text-foreground">Faculty</h3>
        </div>
        <Button variant="secondary" size="sm" onClick={() => setShowAdd(true)} className="gap-1.5">
          <Plus size={14} /> Add faculty
        </Button>
      </div>

      {facultyQ.isLoading ? (
        <Skeleton className="h-40" />
      ) : facultyQ.isError ? (
        <QueryError
          variant="inline"
          detail="Couldn’t load faculty."
          onRetry={() => facultyQ.refetch()}
        />
      ) : (facultyQ.data ?? []).length === 0 ? (
        <p className="text-sm italic text-muted-foreground">
          No faculty yet. Add advisors so research-fit matching can rank them for applicants.
        </p>
      ) : (
        <div className="space-y-2.5">
          {facultyQ.data!.map(f => (
            <FacultyCard key={f.id} faculty={f} />
          ))}
        </div>
      )}

      <Modal
        isOpen={showAdd}
        onClose={() => setShowAdd(false)}
        title="Add faculty advisor"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="tertiary" size="sm" onClick={() => setShowAdd(false)}>
              Cancel
            </Button>
            <Button
              variant="secondary"
              size="sm"
              loading={createMut.isPending}
              disabled={!form.name.trim()}
              onClick={() => createMut.mutate()}
            >
              Add faculty
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <Input
            label="Name"
            value={form.name}
            onChange={e => setForm({ ...form, name: e.target.value })}
            placeholder="Dr Jane Smith"
          />
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Select
              label="Department"
              options={deptOptions}
              value={form.department_id}
              onChange={e => setForm({ ...form, department_id: e.target.value })}
            />
            <Input
              label="Title"
              value={form.title}
              onChange={e => setForm({ ...form, title: e.target.value })}
              placeholder="Associate Professor"
            />
          </div>
          <Input
            label="Email"
            value={form.email}
            onChange={e => setForm({ ...form, email: e.target.value })}
            placeholder="jsmith@university.edu"
          />
          <TagInput
            label="Research areas"
            values={form.research_areas}
            onChange={v => setForm({ ...form, research_areas: v })}
            placeholder="Add an area and press Enter"
          />
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <Input
              label="Openings"
              type="number"
              min={0}
              value={form.openings}
              onChange={e => setForm({ ...form, openings: e.target.value })}
            />
            <div className="flex items-end pb-1">
              <Toggle
                checked={form.accepting_students}
                onChange={v => setForm({ ...form, accepting_students: v })}
                label="Accepting"
              />
            </div>
            <div className="flex items-end pb-1">
              <Toggle
                checked={form.funding_available}
                onChange={v => setForm({ ...form, funding_available: v })}
                label="Funding"
              />
            </div>
          </div>
        </div>
      </Modal>
    </Card>
  )
}
