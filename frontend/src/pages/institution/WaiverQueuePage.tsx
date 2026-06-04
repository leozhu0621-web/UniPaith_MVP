import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { HandCoins, Receipt, RotateCcw, Check, X, Info } from 'lucide-react'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Badge from '../../components/ui/Badge'
import QueryError from '../../components/ui/QueryError'
import Modal from '../../components/ui/Modal'
import Input from '../../components/ui/Input'
import Textarea from '../../components/ui/Textarea'
import Skeleton from '../../components/ui/Skeleton'
import { showToast } from '../../stores/toast-store'
import {
  listWaivers,
  decideWaiver,
  listPayments,
  refundPayment,
  formatMoney,
  type PaymentRow,
} from '../../api/payments'

const BASIS_LABEL: Record<string, string> = {
  fee_waiver_code: 'Fee-waiver code',
  first_gen: 'First-generation',
  income_band: 'Income band',
  nacac_sram: 'NACAC / SRAR',
  other: 'Other',
}

const STATUS_VARIANT: Record<string, 'success' | 'warning' | 'neutral' | 'info' | 'error'> = {
  paid: 'success',
  waived: 'info',
  refunded: 'neutral',
  partially_refunded: 'warning',
  waiver_pending: 'warning',
  due: 'neutral',
  failed: 'error',
}

export default function WaiverQueuePage() {
  const qc = useQueryClient()
  const waiversQ = useQuery({ queryKey: ['waivers', 'pending'], queryFn: () => listWaivers('pending') })
  const paymentsQ = useQuery({ queryKey: ['inst-payments'], queryFn: () => listPayments() })

  const [refundTarget, setRefundTarget] = useState<PaymentRow | null>(null)
  const [refundAmount, setRefundAmount] = useState('')
  const [refundReason, setRefundReason] = useState('')

  const refreshAll = () => {
    qc.invalidateQueries({ queryKey: ['waivers', 'pending'] })
    qc.invalidateQueries({ queryKey: ['inst-payments'] })
  }

  const decideMut = useMutation({
    mutationFn: ({ id, decision, reason }: { id: string; decision: 'approve' | 'deny' | 'request_info'; reason?: string }) =>
      decideWaiver(id, decision, reason),
    onSuccess: (_d, vars) => {
      refreshAll()
      showToast(
        vars.decision === 'approve'
          ? 'Waiver approved'
          : vars.decision === 'deny'
            ? 'Waiver denied'
            : 'Asked the applicant for more info',
        'success',
      )
    },
    onError: (e: unknown) => showToast(e instanceof Error ? e.message : 'Could not record decision', 'error'),
  })

  const refundMut = useMutation({
    mutationFn: () => {
      const cents = refundAmount ? Math.round(parseFloat(refundAmount) * 100) : undefined
      return refundPayment(refundTarget!.payment_id, cents, refundReason || undefined)
    },
    onSuccess: () => {
      refreshAll()
      setRefundTarget(null)
      setRefundAmount('')
      setRefundReason('')
      showToast('Refund issued', 'success')
    },
    onError: (e: unknown) => showToast(e instanceof Error ? e.message : 'Could not issue refund', 'error'),
  })

  const waivers = waiversQ.data ?? []
  const payments = paymentsQ.data ?? []
  const refundable = payments.filter(p => p.refundable_cents > 0)

  return (
    <div className="space-y-6 max-w-4xl">
      {/* ── Fee-waiver queue (§2.3) ── */}
      <section className="space-y-3">
        <div className="flex items-center gap-2">
          <HandCoins size={18} className="text-secondary" />
          <h2 className="text-lg font-bold text-foreground">Fee-waiver requests</h2>
          {waivers.length > 0 && <Badge variant="warning">{waivers.length} pending</Badge>}
        </div>

        {waiversQ.isLoading ? (
          <Skeleton className="h-24 w-full rounded-xl" />
        ) : waiversQ.isError ? (
          <QueryError variant="inline" detail="We couldn't load fee-waiver requests." onRetry={() => waiversQ.refetch()} />
        ) : waivers.length === 0 ? (
          <Card className="p-6 text-center text-sm text-muted-foreground">
            No pending fee-waiver requests. Auto-approved bases never reach this queue.
          </Card>
        ) : (
          waivers.map(w => {
            const evidence = (w.evidence || {}) as { note?: string; url?: string }
            const busy = decideMut.isPending && decideMut.variables?.id === w.payment_id
            return (
              <Card key={w.payment_id} className="p-4">
                <div className="flex items-start justify-between gap-3 flex-wrap">
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-foreground">{w.student_name || 'Applicant'}</p>
                    <p className="text-xs text-muted-foreground">{w.program_name}</p>
                    <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                      <Badge variant="info">{BASIS_LABEL[w.basis || 'other'] || w.basis}</Badge>
                      <span className="text-xs text-muted-foreground">
                        Fee {formatMoney(w.amount, w.currency)}
                      </span>
                    </div>
                    {evidence.note && (
                      <p className="text-xs text-foreground mt-1.5">“{evidence.note}”</p>
                    )}
                    {evidence.url && (
                      <a href={evidence.url} target="_blank" rel="noreferrer" className="text-xs text-secondary hover:underline">
                        View supporting evidence
                      </a>
                    )}
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Button
                      variant="secondary"
                      size="sm"
                      loading={busy}
                      onClick={() => decideMut.mutate({ id: w.payment_id, decision: 'approve' })}
                    >
                      <Check size={14} className="mr-1" /> Approve
                    </Button>
                    <Button
                      variant="tertiary"
                      size="sm"
                      onClick={() => decideMut.mutate({ id: w.payment_id, decision: 'request_info' })}
                    >
                      <Info size={14} className="mr-1" /> More info
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => decideMut.mutate({ id: w.payment_id, decision: 'deny' })}
                    >
                      <X size={14} className="mr-1" /> Deny
                    </Button>
                  </div>
                </div>
              </Card>
            )
          })
        )}
      </section>

      {/* ── Payments & refunds (§5) ── */}
      <section className="space-y-3">
        <div className="flex items-center gap-2">
          <Receipt size={18} className="text-secondary" />
          <h2 className="text-lg font-bold text-foreground">Payments & refunds</h2>
        </div>

        {paymentsQ.isLoading ? (
          <Skeleton className="h-24 w-full rounded-xl" />
        ) : paymentsQ.isError ? (
          <QueryError variant="inline" detail="We couldn't load payments." onRetry={() => paymentsQ.refetch()} />
        ) : payments.length === 0 ? (
          <Card className="p-6 text-center text-sm text-muted-foreground">No payments yet.</Card>
        ) : (
          <Card className="p-0 overflow-hidden">
            <div className="divide-y divide-border">
              {payments.map(p => (
                <div key={p.payment_id} className="flex items-center justify-between gap-3 px-4 py-3">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">{p.student_name || 'Applicant'}</p>
                    <p className="text-xs text-muted-foreground truncate">
                      {p.kind === 'application_fee' ? 'Application fee' : 'Enrollment deposit'} · {p.program_name}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <div className="text-right">
                      <p className="text-sm font-semibold text-foreground tabular-nums">
                        {formatMoney(p.amount, p.currency)}
                      </p>
                      {p.refunded_amount > 0 && (
                        <p className="text-[11px] text-muted-foreground">
                          −{formatMoney(p.refunded_amount, p.currency)} refunded
                        </p>
                      )}
                    </div>
                    <Badge variant={STATUS_VARIANT[p.status] || 'neutral'}>{p.status.replace(/_/g, ' ')}</Badge>
                    {p.refundable_cents > 0 && (
                      <Button
                        variant="tertiary"
                        size="sm"
                        onClick={() => {
                          setRefundTarget(p)
                          setRefundAmount((p.refundable_cents / 100).toString())
                          setRefundReason('')
                        }}
                      >
                        <RotateCcw size={13} className="mr-1" /> Refund
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}
        {refundable.length === 0 && payments.length > 0 && (
          <p className="text-xs text-muted-foreground">No payments are currently refundable.</p>
        )}
      </section>

      {/* ── Refund modal ── */}
      <Modal isOpen={!!refundTarget} onClose={() => setRefundTarget(null)} title="Issue a refund" size="sm">
        {refundTarget && (
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Refunding {refundTarget.student_name || 'this applicant'}'s{' '}
              {refundTarget.kind === 'application_fee' ? 'application fee' : 'enrollment deposit'}. Up to{' '}
              {formatMoney(refundTarget.refundable_cents / 100, refundTarget.currency)} can be refunded.
            </p>
            <Input
              label={`Amount (${refundTarget.currency})`}
              type="number"
              min={0}
              step="1"
              value={refundAmount}
              onChange={e => setRefundAmount(e.target.value)}
            />
            <Textarea
              label="Reason (audited)"
              value={refundReason}
              onChange={e => setRefundReason(e.target.value)}
              placeholder="e.g. refundable-window withdrawal, duplicate, goodwill"
            />
            <div className="flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setRefundTarget(null)}>
                Cancel
              </Button>
              <Button variant="secondary" loading={refundMut.isPending} onClick={() => refundMut.mutate()}>
                Issue refund
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
