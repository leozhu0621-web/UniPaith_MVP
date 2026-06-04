import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, Lightbulb, Plus, Trash2, Wallet } from 'lucide-react'
import {
  buildFundingPackage,
  getFundingBudget,
  getFundingPackage,
  listFundingPools,
  type FundingComponentKind,
  type FundingPackageStatus,
} from '../../../api/graduate'
import Card from '../../../components/ui/Card'
import Badge from '../../../components/ui/Badge'
import Button from '../../../components/ui/Button'
import Input from '../../../components/ui/Input'
import Select from '../../../components/ui/Select'
import Skeleton from '../../../components/ui/Skeleton'
import QueryError from '../../../components/ui/QueryError'
import AIBadge from '../../../components/ui/AIBadge'
import { showToast } from '../../../stores/toast-store'
import { COMPONENT_KIND_OPTIONS, fmtMoney } from './constants'

interface DraftComponent {
  kind: FundingComponentKind
  amount: string
  source_pool_id: string
  years: number[]
}

const YEAR_CHOICES = [1, 2, 3, 4, 5]

function apiError(e: unknown): string {
  const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (detail && typeof detail === 'object' && 'message' in detail)
    return String((detail as { message?: string }).message)
  return 'Could not save the funding package'
}

export default function FundingBuilder({
  applicationId,
  currency = 'USD',
}: {
  applicationId: string
  currency?: string
}) {
  const qc = useQueryClient()
  const poolsQ = useQuery({ queryKey: ['grad-pools'], queryFn: () => listFundingPools() })
  const budgetQ = useQuery({ queryKey: ['grad-budget'], queryFn: () => getFundingBudget() })
  const packageQ = useQuery({
    queryKey: ['grad-package', applicationId],
    queryFn: () => getFundingPackage(applicationId),
  })

  const [draft, setDraft] = useState<DraftComponent[]>([])
  const [notes, setNotes] = useState('')

  useEffect(() => {
    const pkg = packageQ.data
    if (pkg) {
      setDraft(
        pkg.components.map(c => ({
          kind: c.kind,
          amount: String(c.amount),
          source_pool_id: c.source_pool_id ?? '',
          years: c.years?.length ? c.years : [1],
        })),
      )
      setNotes(pkg.notes ?? '')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [packageQ.data?.application_id, packageQ.dataUpdatedAt])

  const pools = useMemo(() => poolsQ.data ?? [], [poolsQ.data])
  const poolOptions = useMemo(
    () => [{ value: '', label: '— Select a pool —' }, ...pools.map(p => ({ value: p.id, label: p.name }))],
    [pools],
  )

  const total = draft.reduce((s, c) => s + (Number(c.amount) || 0), 0)
  const multiYear = draft.some(c => c.years.some(y => y > 1))
  const hasNegative = draft.some(c => Number(c.amount) < 0)

  const saveMut = useMutation({
    mutationFn: (status: FundingPackageStatus) =>
      buildFundingPackage(applicationId, {
        status,
        currency,
        notes: notes || null,
        components: draft.map(c => ({
          kind: c.kind,
          amount: Number(c.amount) || 0,
          source_pool_id: c.source_pool_id || null,
          years: c.years.length ? c.years : [1],
        })),
      }),
    onSuccess: (_data, status) => {
      showToast(
        status === 'finalized'
          ? 'Funding package finalized'
          : status === 'proposed'
            ? 'Funding package proposed'
            : 'Draft saved',
        'success',
      )
      qc.invalidateQueries({ queryKey: ['grad-package', applicationId] })
      qc.invalidateQueries({ queryKey: ['grad-budget'] })
      qc.invalidateQueries({ queryKey: ['grad-budget-dept'] })
    },
    onError: (e: unknown) => showToast(apiError(e), 'error'),
  })

  if (poolsQ.isLoading || budgetQ.isLoading || packageQ.isLoading) return <Skeleton className="h-72" />
  if (poolsQ.isError || budgetQ.isError || packageQ.isError)
    return (
      <Card className="p-5">
        <QueryError
          variant="inline"
          detail="Couldn’t load the funding package."
          onRetry={() => {
            poolsQ.refetch()
            budgetQ.refetch()
            packageQ.refetch()
          }}
        />
      </Card>
    )

  const pkg = packageQ.data
  const analysis = pkg?.analysis
  const budget = budgetQ.data

  const addRow = () =>
    setDraft([...draft, { kind: 'RA', amount: '', source_pool_id: '', years: [1] }])
  const removeRow = (i: number) => setDraft(draft.filter((_, x) => x !== i))
  const patchRow = (i: number, patch: Partial<DraftComponent>) =>
    setDraft(draft.map((c, x) => (x === i ? { ...c, ...patch } : c)))
  const toggleYear = (i: number, y: number) => {
    const cur = draft[i].years
    const next = cur.includes(y) ? cur.filter(v => v !== y) : [...cur, y]
    patchRow(i, { years: next.length ? next : [1] })
  }

  return (
    <Card className="p-5">
      <div className="mb-4 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-secondary">
            <Wallet size={16} />
          </span>
          <h3 className="text-sm font-semibold text-foreground">Funding package</h3>
          {pkg && (
            <Badge variant={pkg.status === 'finalized' ? 'success' : 'neutral'}>{pkg.status}</Badge>
          )}
          {multiYear && <Badge variant="info">Multi-year</Badge>}
        </div>
        <span className="text-sm font-semibold tabular-nums text-foreground">
          {fmtMoney(total, currency)}
        </span>
      </div>

      {/* Component rows */}
      <div className="space-y-3">
        {draft.length === 0 && (
          <p className="text-sm italic text-muted-foreground">
            No funding components yet. Add a TA, RA, fellowship, waiver, or stipend.
          </p>
        )}
        {draft.map((c, i) => (
          <div key={i} className="rounded-lg border border-border bg-muted/30 p-3">
            <div className="flex flex-wrap items-end gap-3">
              <div className="w-48">
                <Select
                  label="Type"
                  options={COMPONENT_KIND_OPTIONS}
                  value={c.kind}
                  onChange={e => patchRow(i, { kind: e.target.value as FundingComponentKind })}
                />
              </div>
              <div className="w-32">
                <Input
                  label="Amount"
                  type="number"
                  min={0}
                  value={c.amount}
                  onChange={e => patchRow(i, { amount: e.target.value })}
                  placeholder="0"
                  error={Number(c.amount) < 0 ? 'Must be ≥ 0' : undefined}
                />
              </div>
              <div className="w-52">
                <Select
                  label="Source pool"
                  options={poolOptions}
                  value={c.source_pool_id}
                  onChange={e => patchRow(i, { source_pool_id: e.target.value })}
                />
              </div>
              <button
                type="button"
                onClick={() => removeRow(i)}
                className="mb-1 rounded-md p-2 text-muted-foreground hover:bg-error-soft/60 hover:text-error"
                aria-label="Remove component"
              >
                <Trash2 size={15} />
              </button>
            </div>
            <div className="mt-2 flex items-center gap-1.5">
              <span className="text-xs text-muted-foreground">Years:</span>
              {YEAR_CHOICES.map(y => (
                <button
                  key={y}
                  type="button"
                  onClick={() => toggleYear(i, y)}
                  className={`h-6 w-6 rounded text-xs font-medium tabular-nums transition-colors ${
                    c.years.includes(y)
                      ? 'bg-secondary text-secondary-foreground'
                      : 'bg-muted text-muted-foreground hover:bg-muted/70'
                  }`}
                >
                  {y}
                </button>
              ))}
            </div>
          </div>
        ))}
        <Button variant="ghost" size="sm" onClick={addRow} className="gap-1.5">
          <Plus size={14} /> Add component
        </Button>
      </div>

      {/* Pool budgets reference */}
      {budget && budget.pools.length > 0 && (
        <div className="mt-5 space-y-2">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Pool budgets
          </p>
          {budget.pools.map(p => {
            const pct = p.budget > 0 ? Math.min(100, (p.committed / p.budget) * 100) : 0
            return (
              <div key={p.id}>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-foreground">{p.name}</span>
                  <span className={`tabular-nums ${p.over ? 'text-error' : 'text-muted-foreground'}`}>
                    {fmtMoney(p.committed, p.currency)} / {fmtMoney(p.budget, p.currency)}
                  </span>
                </div>
                <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className={`h-full rounded-full ${p.over ? 'bg-error' : 'bg-secondary'}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* AI advisory (FundingScenarioHelper §5) */}
      {analysis && (analysis.warnings.length > 0 || analysis.suggestions.length > 0) && (
        <div className="mt-4 rounded-lg border border-warning/40 bg-warning-soft px-4 py-3">
          <div className="mb-1 flex items-center gap-2 text-sm font-medium text-warning">
            <AlertTriangle size={15} /> Funding check <AIBadge />
          </div>
          {analysis.warnings.map((w, i) => (
            <p key={`w${i}`} className="text-xs text-warning">
              • {w}
            </p>
          ))}
          {analysis.suggestions.map((s, i) => (
            <p key={`s${i}`} className="mt-1 flex items-start gap-1 text-xs text-muted-foreground">
              <Lightbulb size={12} className="mt-0.5 shrink-0" /> {s}
            </p>
          ))}
        </div>
      )}

      {/* Save actions */}
      <div className="mt-5 flex flex-wrap items-center justify-end gap-2">
        {hasNegative && (
          <span className="mr-auto text-xs text-error">Funding amounts can’t be negative.</span>
        )}
        <Button
          variant="ghost"
          size="sm"
          disabled={hasNegative}
          loading={saveMut.isPending && saveMut.variables === 'draft'}
          onClick={() => saveMut.mutate('draft')}
        >
          Save draft
        </Button>
        <Button
          variant="tertiary"
          size="sm"
          disabled={hasNegative}
          loading={saveMut.isPending && saveMut.variables === 'proposed'}
          onClick={() => saveMut.mutate('proposed')}
        >
          Propose
        </Button>
        <Button
          variant="secondary"
          size="sm"
          disabled={hasNegative}
          loading={saveMut.isPending && saveMut.variables === 'finalized'}
          onClick={() => saveMut.mutate('finalized')}
        >
          Finalize
        </Button>
      </div>
    </Card>
  )
}
