import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Building2, ChevronRight, GraduationCap, Plus } from 'lucide-react'
import {
  createDepartment,
  getGraduateSummary,
  listDepartments,
  type DepartmentSummary,
} from '../../../api/graduate'
import Card from '../../../components/ui/Card'
import Button from '../../../components/ui/Button'
import Input from '../../../components/ui/Input'
import Textarea from '../../../components/ui/Textarea'
import Modal from '../../../components/ui/Modal'
import Skeleton from '../../../components/ui/Skeleton'
import EmptyState from '../../../components/ui/EmptyState'
import QueryError from '../../../components/ui/QueryError'
import { showToast } from '../../../stores/toast-store'
import { fmtMoney } from './constants'
import FundingPoolsPanel from './FundingPoolsPanel'
import FacultyRoster from './FacultyRoster'

function Kpi({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <div className="rounded-lg border border-border bg-background px-4 py-3">
      <div className="text-2xl font-semibold tabular-nums text-foreground">{value}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
      {hint && <div className="mt-0.5 text-[11px] text-muted-foreground">{hint}</div>}
    </div>
  )
}

function DepartmentCard({ dept }: { dept: DepartmentSummary }) {
  const navigate = useNavigate()
  const pct = dept.funding_budget > 0 ? Math.min(100, (dept.funding_committed / dept.funding_budget) * 100) : 0
  return (
    <button
      type="button"
      onClick={() => navigate(`/i/departments/${dept.id}`)}
      className="block w-full rounded-lg border border-border bg-background p-4 text-left transition-colors hover:border-secondary/40"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-secondary">
            <Building2 size={16} />
          </span>
          <span className="font-medium text-foreground">{dept.name}</span>
          {dept.code && (
            <span className="rounded bg-muted px-1.5 py-0.5 text-[11px] text-muted-foreground">
              {dept.code}
            </span>
          )}
        </div>
        <ChevronRight size={16} className="text-muted-foreground" />
      </div>
      <div className="mt-3 flex gap-4 text-xs text-muted-foreground">
        <span>
          <span className="font-semibold text-foreground">{dept.program_count}</span> programs
        </span>
        <span>
          <span className="font-semibold text-foreground">{dept.faculty_count}</span> faculty
        </span>
      </div>
      {dept.funding_budget > 0 && (
        <div className="mt-3">
          <div className="flex items-center justify-between text-[11px] text-muted-foreground">
            <span>Funding</span>
            <span className="tabular-nums">
              {fmtMoney(dept.funding_committed)} / {fmtMoney(dept.funding_budget)}
            </span>
          </div>
          <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-muted">
            <div className="h-full rounded-full bg-secondary" style={{ width: `${pct}%` }} />
          </div>
        </div>
      )}
    </button>
  )
}

export default function GraduatePage() {
  const qc = useQueryClient()
  const summaryQ = useQuery({ queryKey: ['grad-summary'], queryFn: getGraduateSummary })
  const deptsQ = useQuery({ queryKey: ['grad-departments'], queryFn: listDepartments })

  const [showAdd, setShowAdd] = useState(false)
  const [form, setForm] = useState({ name: '', code: '', description: '' })

  const createMut = useMutation({
    mutationFn: () =>
      createDepartment({
        name: form.name.trim(),
        code: form.code || undefined,
        description: form.description || undefined,
      }),
    onSuccess: () => {
      showToast('Department created', 'success')
      setShowAdd(false)
      setForm({ name: '', code: '', description: '' })
      qc.invalidateQueries({ queryKey: ['grad-departments'] })
      qc.invalidateQueries({ queryKey: ['grad-summary'] })
    },
    onError: () => showToast('Could not create department', 'error'),
  })

  const summary = summaryQ.data
  const departments = deptsQ.data ?? []
  const deptOptions = departments.map(d => ({ id: d.id, name: d.name }))

  return (
    <div className="space-y-5">
      <header>
        <div className="flex items-center gap-2">
          <span className="text-secondary">
            <GraduationCap size={20} />
          </span>
          <h2 className="text-lg font-semibold text-foreground">Graduate &amp; PhD admissions</h2>
        </div>
      </header>

      {/* KPIs */}
      {summaryQ.isLoading ? (
        <Skeleton className="h-20" />
      ) : summary ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          <Kpi label="Departments" value={summary.department_count} />
          <Kpi label="Faculty" value={summary.faculty_count} />
          <Kpi label="Graduate applicants" value={summary.graduate_application_count} />
          <Kpi label="Pending recommendations" value={summary.pending_recommendations} />
          <Kpi
            label="Funding committed"
            value={fmtMoney(summary.funding.total_committed)}
            hint={`of ${fmtMoney(summary.funding.total_budget)}`}
          />
        </div>
      ) : null}

      {/* Departments */}
      <Card pad={false} className="p-5">
        <div className="mb-4 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="text-secondary">
              <Building2 size={16} />
            </span>
            <h3 className="text-sm font-semibold text-foreground">Departments</h3>
          </div>
          <Button variant="secondary" size="sm" onClick={() => setShowAdd(true)} className="gap-1.5">
            <Plus size={14} /> New department
          </Button>
        </div>
        {deptsQ.isLoading ? (
          <Skeleton className="h-32" />
        ) : deptsQ.isError ? (
          <QueryError
            variant="inline"
            detail="Couldn’t load departments."
            onRetry={() => deptsQ.refetch()}
          />
        ) : departments.length === 0 ? (
          <EmptyState
            icon={<Building2 size={28} />}
            title="No departments yet"
          />
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {departments.map(d => (
              <DepartmentCard key={d.id} dept={d} />
            ))}
          </div>
        )}
      </Card>

      {/* Funding pools (institution-wide) */}
      <FundingPoolsPanel departments={deptOptions} />

      {/* Faculty roster (institution-wide) */}
      <FacultyRoster departments={deptOptions} />

      <Modal
        isOpen={showAdd}
        onClose={() => setShowAdd(false)}
        title="New department"
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
              Create department
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <Input
            label="Department name"
            value={form.name}
            onChange={e => setForm({ ...form, name: e.target.value })}
            placeholder="e.g. Computer Science"
          />
          <Input
            label="Code"
            value={form.code}
            onChange={e => setForm({ ...form, code: e.target.value })}
            placeholder="e.g. CS"
          />
          <Textarea
            label="Description"
            value={form.description}
            onChange={e => setForm({ ...form, description: e.target.value })}
            rows={2}
            placeholder="Optional"
          />
        </div>
      </Modal>
    </div>
  )
}
