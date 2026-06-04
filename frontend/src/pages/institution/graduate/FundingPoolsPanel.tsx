import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Wallet } from 'lucide-react'
import {
  createFundingPool,
  getFundingBudget,
  updateFundingPool,
  type FundingPoolBudget,
  type FundingPoolKind,
} from '../../../api/graduate'
import Card from '../../../components/ui/Card'
import Button from '../../../components/ui/Button'
import Input from '../../../components/ui/Input'
import Select from '../../../components/ui/Select'
import Modal from '../../../components/ui/Modal'
import Skeleton from '../../../components/ui/Skeleton'
import QueryError from '../../../components/ui/QueryError'
import { showToast } from '../../../stores/toast-store'
import { POOL_KIND_LABELS, POOL_KIND_OPTIONS, fmtMoney } from './constants'

interface DeptOption {
  id: string
  name: string
}

interface PoolForm {
  id?: string
  name: string
  kind: FundingPoolKind
  total_budget: string
  department_id: string
  currency: string
}

const BLANK = (deptId?: string): PoolForm => ({
  name: '',
  kind: 'department',
  total_budget: '',
  department_id: deptId ?? '',
  currency: 'USD',
})

export default function FundingPoolsPanel({
  departmentId,
  departments,
}: {
  departmentId?: string
  departments: DeptOption[]
}) {
  const qc = useQueryClient()
  const budgetQ = useQuery({
    queryKey: ['grad-budget-dept', departmentId ?? 'all'],
    queryFn: () => getFundingBudget(departmentId),
  })
  const [form, setForm] = useState<PoolForm | null>(null)

  const saveMut = useMutation({
    mutationFn: (f: PoolForm) => {
      const payload = {
        name: f.name.trim(),
        kind: f.kind,
        total_budget: Number(f.total_budget) || 0,
        department_id: f.department_id || null,
        currency: f.currency || 'USD',
      }
      return f.id ? updateFundingPool(f.id, payload) : createFundingPool(payload)
    },
    onSuccess: () => {
      showToast('Funding pool saved', 'success')
      setForm(null)
      qc.invalidateQueries({ queryKey: ['grad-budget-dept'] })
      qc.invalidateQueries({ queryKey: ['grad-budget'] })
      qc.invalidateQueries({ queryKey: ['grad-pools'] })
    },
    onError: () => showToast('Could not save pool', 'error'),
  })

  const openEdit = (p: FundingPoolBudget) =>
    setForm({
      id: p.id,
      name: p.name,
      kind: p.kind,
      total_budget: String(p.budget),
      department_id: p.department_id ?? '',
      currency: p.currency,
    })

  const deptOptions = [
    { value: '', label: '— Institution-wide —' },
    ...departments.map(d => ({ value: d.id, label: d.name })),
  ]

  const budget = budgetQ.data

  return (
    <Card className="p-5">
      <div className="mb-4 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-secondary">
            <Wallet size={16} />
          </span>
          <h3 className="text-sm font-semibold text-foreground">Funding pools</h3>
          {budget && (
            <span className="text-xs text-muted-foreground">
              {fmtMoney(budget.total_committed)} / {fmtMoney(budget.total_budget)} committed
            </span>
          )}
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => setForm(BLANK(departmentId))}
          className="gap-1.5"
        >
          <Plus size={14} /> New pool
        </Button>
      </div>

      {budgetQ.isLoading ? (
        <Skeleton className="h-32" />
      ) : budgetQ.isError ? (
        <QueryError
          variant="inline"
          detail="Couldn’t load funding pools."
          onRetry={() => budgetQ.refetch()}
        />
      ) : !budget || budget.pools.length === 0 ? (
        <p className="text-sm italic text-muted-foreground">
          No funding pools yet. Add a department, grant, or fellowship pool to budget packages
          against.
        </p>
      ) : (
        <div className="space-y-3">
          {budget.pools.map(p => {
            const pct = p.budget > 0 ? Math.min(100, (p.committed / p.budget) * 100) : 0
            return (
              <button
                key={p.id}
                type="button"
                onClick={() => openEdit(p)}
                className="block w-full rounded-lg border border-border bg-background p-3 text-left transition-colors hover:border-secondary/40"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-foreground">{p.name}</span>
                    <span className="rounded bg-muted px-1.5 py-0.5 text-[11px] text-muted-foreground">
                      {POOL_KIND_LABELS[p.kind]}
                    </span>
                  </div>
                  <span className={`text-sm tabular-nums ${p.over ? 'text-error' : 'text-muted-foreground'}`}>
                    {fmtMoney(p.committed, p.currency)} / {fmtMoney(p.budget, p.currency)}
                  </span>
                </div>
                <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className={`h-full rounded-full ${p.over ? 'bg-error' : 'bg-secondary'}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <div className="mt-1 text-right text-xs text-muted-foreground">
                  {p.over ? (
                    <span className="text-error">Over budget by {fmtMoney(-p.remaining, p.currency)}</span>
                  ) : (
                    <span>{fmtMoney(p.remaining, p.currency)} remaining</span>
                  )}
                </div>
              </button>
            )
          })}
        </div>
      )}

      <Modal
        isOpen={form !== null}
        onClose={() => setForm(null)}
        title={form?.id ? 'Edit funding pool' : 'New funding pool'}
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="tertiary" size="sm" onClick={() => setForm(null)}>
              Cancel
            </Button>
            <Button
              variant="secondary"
              size="sm"
              loading={saveMut.isPending}
              disabled={!form?.name.trim() || Number(form?.total_budget) < 0}
              onClick={() => form && saveMut.mutate(form)}
            >
              Save pool
            </Button>
          </div>
        }
      >
        {form && (
          <div className="space-y-4">
            <Input
              label="Pool name"
              value={form.name}
              onChange={e => setForm({ ...form, name: e.target.value })}
              placeholder="e.g. Department TA budget"
            />
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Select
                label="Kind"
                options={POOL_KIND_OPTIONS}
                value={form.kind}
                onChange={e => setForm({ ...form, kind: e.target.value as FundingPoolKind })}
              />
              <Input
                label="Total budget"
                type="number"
                min={0}
                value={form.total_budget}
                onChange={e => setForm({ ...form, total_budget: e.target.value })}
                placeholder="0"
                error={Number(form.total_budget) < 0 ? 'Must be ≥ 0' : undefined}
              />
            </div>
            <Select
              label="Department"
              options={deptOptions}
              value={form.department_id}
              onChange={e => setForm({ ...form, department_id: e.target.value })}
            />
          </div>
        )}
      </Modal>
    </Card>
  )
}
