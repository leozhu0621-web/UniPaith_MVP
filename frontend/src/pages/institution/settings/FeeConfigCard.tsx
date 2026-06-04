import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { HandCoins, Landmark } from 'lucide-react'
import Card from '../../../components/ui/Card'
import Input from '../../../components/ui/Input'
import Toggle from '../../../components/ui/Toggle'
import Button from '../../../components/ui/Button'
import Select from '../../../components/ui/Select'
import Badge from '../../../components/ui/Badge'
import Skeleton from '../../../components/ui/Skeleton'
import QueryError from '../../../components/ui/QueryError'
import { showToast } from '../../../stores/toast-store'
import { getFeeConfig, updateFeeConfig, type FeeConfig } from '../../../api/payments'

// Spec 39 §2.1 — applicant-facing fee/deposit collection config. Amounts edited
// in whole currency units; stored as cents.

const WAIVER_BASES: { key: string; label: string }[] = [
  { key: 'fee_waiver_code', label: 'Verified fee-waiver code' },
  { key: 'first_gen', label: 'First-generation' },
  { key: 'income_band', label: 'Income band' },
  { key: 'nacac_sram', label: 'NACAC / SRAR waiver' },
  { key: 'other', label: 'Other (always manual)' },
]

const CURRENCIES = ['USD', 'GBP', 'EUR', 'CAD', 'AUD'].map(c => ({ value: c, label: c }))

export default function FeeConfigCard() {
  const qc = useQueryClient()
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ['fee-config'], queryFn: getFeeConfig })
  const [cfg, setCfg] = useState<FeeConfig | null>(null)
  useEffect(() => {
    if (data) setCfg(data)
  }, [data])

  const save = useMutation({
    mutationFn: () =>
      updateFeeConfig({
        application_fee: cfg!.application_fee,
        waiver: cfg!.waiver,
        enrollment_deposit: cfg!.enrollment_deposit,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['fee-config'] })
      showToast('Fee settings saved', 'success')
    },
    onError: (e: unknown) => showToast(e instanceof Error ? e.message : 'Could not save', 'error'),
  })

  if (isError && !cfg) {
    return (
      <Card className="p-6">
        <QueryError detail="We couldn't load your fee settings." onRetry={() => refetch()} />
      </Card>
    )
  }

  if (isLoading || !cfg) {
    return (
      <Card className="p-6">
        <Skeleton className="h-40" />
      </Card>
    )
  }

  const af = cfg.application_fee
  const dep = cfg.enrollment_deposit
  const dollars = (cents: number) => (cents / 100).toString()
  const toCents = (v: string) => Math.max(0, Math.round(parseFloat(v || '0') * 100))

  const toggleAuto = (key: string) =>
    setCfg(c => {
      if (!c) return c
      const has = c.waiver.auto_rules.includes(key)
      const auto_rules = has
        ? c.waiver.auto_rules.filter(r => r !== key)
        : [...c.waiver.auto_rules, key]
      return { ...c, waiver: { ...c.waiver, auto_rules } }
    })

  return (
    <Card className="p-5 sm:p-6 space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <HandCoins size={18} className="text-secondary" />
          <h3 className="text-sm font-semibold text-foreground">Application fees & deposits</h3>
        </div>
        <Badge variant={cfg.provider === 'stripe' ? 'success' : 'neutral'}>
          {cfg.provider === 'stripe' ? 'Stripe live' : 'Test mode (mock)'}
        </Badge>
      </div>
      <p className="-mt-3 text-xs text-muted-foreground">
        Collect application fees and enrollment deposits from applicants. In test mode no real
        money moves — Stripe goes live per environment once your account is connected.
      </p>

      {/* Application fee */}
      <section className="border-t border-border pt-4 space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-[13px] font-semibold text-foreground">Application fee</h4>
            <p className="text-xs text-muted-foreground">Charged when an applicant submits.</p>
          </div>
          <Toggle
            checked={af.enabled}
            label="Application fee enabled"
            onChange={v => setCfg(c => (c ? { ...c, application_fee: { ...c.application_fee, enabled: v } } : c))}
          />
        </div>
        {af.enabled && (
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Amount"
              type="number"
              min={0}
              step="1"
              value={dollars(af.amount_cents)}
              onChange={e =>
                setCfg(c => (c ? { ...c, application_fee: { ...c.application_fee, amount_cents: toCents(e.target.value) } } : c))
              }
            />
            <Select
              label="Currency"
              value={af.currency}
              options={CURRENCIES}
              onChange={e =>
                setCfg(c => (c ? { ...c, application_fee: { ...c.application_fee, currency: e.target.value } } : c))
              }
            />
          </div>
        )}
      </section>

      {/* Waiver policy */}
      {af.enabled && (
        <section className="border-t border-border pt-4 space-y-3">
          <div>
            <h4 className="text-[13px] font-semibold text-foreground">Fee-waiver policy</h4>
            <p className="text-xs text-muted-foreground">
              Equity matters — the waiver path is offered as prominently as paying.
            </p>
          </div>
          <Select
            label="When a waiver is requested"
            value={cfg.waiver.policy}
            options={[
              { value: 'allow_and_reconcile', label: 'Allow submission, reconcile later (recommended)' },
              { value: 'block_until_approved', label: 'Block submission until approved' },
            ]}
            onChange={e =>
              setCfg(c =>
                c ? { ...c, waiver: { ...c.waiver, policy: e.target.value as FeeConfig['waiver']['policy'] } } : c,
              )
            }
          />
          <div>
            <p className="text-[13px] font-medium text-foreground mb-2">Auto-approve these bases</p>
            <div className="flex flex-wrap gap-2">
              {WAIVER_BASES.map(b => {
                const on = cfg.waiver.auto_rules.includes(b.key)
                const manualOnly = b.key === 'other'
                return (
                  <button
                    key={b.key}
                    type="button"
                    disabled={manualOnly}
                    onClick={() => toggleAuto(b.key)}
                    className={`px-3 py-1.5 text-xs rounded-full border transition-colors ${
                      manualOnly
                        ? 'border-border text-muted-foreground cursor-not-allowed opacity-60'
                        : on
                          ? 'bg-secondary text-secondary-foreground border-secondary'
                          : 'bg-card text-muted-foreground border-border hover:border-secondary/40'
                    }`}
                  >
                    {b.label}
                  </button>
                )
              })}
            </div>
            <p className="text-xs text-muted-foreground mt-1.5">
              Unselected bases route to your waiver queue for a manual decision.
            </p>
          </div>
        </section>
      )}

      {/* Enrollment deposit */}
      <section className="border-t border-border pt-4 space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-[13px] font-semibold text-foreground flex items-center gap-1.5">
              <Landmark size={14} className="text-muted-foreground" /> Enrollment deposit
            </h4>
            <p className="text-xs text-muted-foreground">Paid by admitted students to confirm a spot.</p>
          </div>
          <Toggle
            checked={dep.enabled}
            label="Enrollment deposit enabled"
            onChange={v => setCfg(c => (c ? { ...c, enrollment_deposit: { ...c.enrollment_deposit, enabled: v } } : c))}
          />
        </div>
        {dep.enabled && (
          <>
            <div className="grid grid-cols-3 gap-3">
              <Input
                label="Amount"
                type="number"
                min={0}
                step="1"
                value={dollars(dep.amount_cents)}
                onChange={e =>
                  setCfg(c => (c ? { ...c, enrollment_deposit: { ...c.enrollment_deposit, amount_cents: toCents(e.target.value) } } : c))
                }
              />
              <Select
                label="Currency"
                value={dep.currency}
                options={CURRENCIES}
                onChange={e =>
                  setCfg(c => (c ? { ...c, enrollment_deposit: { ...c.enrollment_deposit, currency: e.target.value } } : c))
                }
              />
              <Input
                label="Deadline (days)"
                type="number"
                min={0}
                value={String(dep.deadline_days)}
                onChange={e =>
                  setCfg(c =>
                    c
                      ? { ...c, enrollment_deposit: { ...c.enrollment_deposit, deadline_days: Math.max(0, parseInt(e.target.value || '0', 10)) } }
                      : c,
                  )
                }
              />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[13px] text-foreground">Refundable within the deposit window</span>
              <Toggle
                checked={dep.refundable}
                label="Deposit refundable"
                onChange={v => setCfg(c => (c ? { ...c, enrollment_deposit: { ...c.enrollment_deposit, refundable: v } } : c))}
              />
            </div>
          </>
        )}
      </section>

      <div className="flex justify-end border-t border-border pt-4">
        <Button variant="secondary" loading={save.isPending} onClick={() => save.mutate()}>
          Save fee settings
        </Button>
      </div>
    </Card>
  )
}
