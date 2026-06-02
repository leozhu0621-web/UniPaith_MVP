import apiClient from './client'

// Spec 39 · Fees & Payments. Views come back as plain objects (mirrors the
// enrollment API); only the shapes the UI reads are typed here.

export interface PaymentWaiver {
  requested: boolean
  basis: string | null
  approved: boolean | null
  note?: string | null
}

export interface FeeView {
  kind: 'application_fee'
  required: boolean
  status: string // due | processing | paid | waived | waiver_pending | waiver_denied | refunded | partially_refunded | failed
  amount: number
  amount_cents: number
  currency: string
  waiver_policy: 'allow_and_reconcile' | 'block_until_approved'
  auto_rules: string[]
  waiver: PaymentWaiver | null
  paid_at: string | null
  refunded_amount: number | null
  payment_id: string | null
}

export interface DepositView {
  kind: 'enrollment_deposit'
  required: boolean
  payable: boolean
  status: string
  amount: number
  amount_cents: number
  currency: string
  refundable: boolean
  paid_at: string | null
  refunded_amount: number | null
  payment_id: string | null
}

export interface CostTracker {
  application_id: string
  payments_enabled: boolean
  fee: FeeView | null
  deposit: DepositView | null
}

export interface CheckoutSession {
  payment_id: string
  provider: string
  inline: boolean
  checkout_url: string | null
  publishable_key: string | null
  amount: number
  amount_cents: number
  currency: string
  kind: string
  status: string
}

export interface WaiverQueueItem {
  payment_id: string
  application_id: string
  student_name: string | null
  program_id: string
  program_name: string
  basis: string | null
  evidence: Record<string, unknown> | null
  status: string
  approved: boolean | null
  amount: number
  currency: string
  requested_at: string | null
  decided_at: string | null
}

export interface PaymentRow {
  payment_id: string
  application_id: string
  student_name: string | null
  program_name: string
  kind: string
  status: string
  amount: number
  amount_cents: number
  refunded_amount: number
  currency: string
  paid_at: string | null
  refundable_cents: number
}

export interface FeeConfig {
  application_fee: { enabled: boolean; amount_cents: number; currency: string }
  waiver: { policy: 'allow_and_reconcile' | 'block_until_approved'; auto_rules: string[] }
  enrollment_deposit: {
    enabled: boolean
    amount_cents: number
    currency: string
    deadline_days: number
    refundable: boolean
    non_refundable_cents: number
  }
  stripe_connect_account_id: string | null
  provider: string
  publishable_key: string | null
}

// Mirrors services/payments/config.is_fee_clear — whether the fee still blocks submit.
export const isFeeClear = (fee?: FeeView | null): boolean => {
  if (!fee || !fee.required) return true
  if (fee.status === 'paid' || fee.status === 'waived') return true
  return fee.status === 'waiver_pending' && fee.waiver_policy === 'allow_and_reconcile'
}

export const formatMoney = (amount: number, currency: string): string => {
  try {
    return new Intl.NumberFormat(undefined, { style: 'currency', currency }).format(amount)
  } catch {
    return `${currency} $${(amount ?? 0).toFixed(2)}`
  }
}

// Spec 39 §8 — "Receipts plain + exportable". Builds a plain-text receipt and
// triggers a download. No PII beyond what the student already sees.
export function downloadReceipt(opts: {
  kind: string
  amount: number
  currency: string
  status: string
  paidAt: string | null
  refundedAmount?: number | null
  programName?: string
  institutionName?: string
  reference?: string | null
}): void {
  const label = opts.kind === 'application_fee' ? 'Application fee' : 'Enrollment deposit'
  const lines = [
    'UniPaith — Payment Receipt',
    '==========================',
    `Item:        ${label}`,
    opts.programName ? `Program:     ${opts.programName}` : '',
    opts.institutionName ? `Institution: ${opts.institutionName}` : '',
    `Amount:      ${formatMoney(opts.amount, opts.currency)} ${opts.currency}`,
    `Status:      ${opts.status.replace(/_/g, ' ')}`,
    opts.paidAt ? `Paid:        ${new Date(opts.paidAt).toLocaleString()}` : '',
    opts.refundedAmount ? `Refunded:    ${formatMoney(opts.refundedAmount, opts.currency)}` : '',
    opts.reference ? `Reference:   ${opts.reference}` : '',
    '',
    'Keep this receipt for your records.',
  ].filter(Boolean)
  const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `unipaith-receipt-${opts.kind}.txt`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

// ── Student ──────────────────────────────────────────────────────────────

export const getCostTracker = (appId: string) =>
  apiClient.get(`/payments/applications/${appId}`).then(r => r.data as CostTracker)

export const payApplicationFee = (appId: string) =>
  apiClient.post(`/payments/applications/${appId}/pay-fee`).then(r => r.data as CheckoutSession)

export const requestFeeWaiver = (
  appId: string,
  basis: string,
  note?: string,
  evidenceUrl?: string,
) =>
  apiClient
    .post(`/payments/applications/${appId}/request-waiver`, {
      basis,
      note: note || null,
      evidence_url: evidenceUrl || null,
    })
    .then(r => r.data as CostTracker)

export const payEnrollmentDeposit = (appId: string) =>
  apiClient.post(`/payments/applications/${appId}/pay-deposit`).then(r => r.data as CheckoutSession)

export const confirmMockPayment = (paymentId: string) =>
  apiClient.post(`/payments/${paymentId}/confirm-mock`).then(r => r.data as CostTracker)

// ── Institution ────────────────────────────────────────────────────────────

export const getFeeConfig = () =>
  apiClient.get('/payments/institution/fee-config').then(r => r.data as FeeConfig)

export const updateFeeConfig = (payload: Partial<Omit<FeeConfig, 'provider' | 'publishable_key'>>) =>
  apiClient.put('/payments/institution/fee-config', payload).then(r => r.data as FeeConfig)

export const listWaivers = (status: 'pending' | 'decided' | 'all' = 'pending') =>
  apiClient
    .get('/payments/institution/waivers', { params: { status } })
    .then(r => r.data as WaiverQueueItem[])

export const decideWaiver = (
  paymentId: string,
  decision: 'approve' | 'deny' | 'request_info',
  reason?: string,
) =>
  apiClient
    .post(`/payments/institution/waivers/${paymentId}/decide`, { decision, reason: reason || null })
    .then(r => r.data)

export const listPayments = (kind?: 'application_fee' | 'enrollment_deposit') =>
  apiClient
    .get('/payments/institution/payments', { params: kind ? { kind } : undefined })
    .then(r => r.data as PaymentRow[])

export const refundPayment = (paymentId: string, amountCents?: number | null, reason?: string) =>
  apiClient
    .post(`/payments/institution/payments/${paymentId}/refund`, {
      amount_cents: amountCents ?? null,
      reason: reason || null,
    })
    .then(r => r.data)
