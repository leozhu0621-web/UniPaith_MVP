// Billing / monetization types (Spec 06 §4). Mirror of the backend
// BillingService.get_status payload + institution usage.

export type Plan = 'trial' | 'free' | 'plus'

export type Feature =
  | 'profile'
  | 'baseline_readiness'
  | 'limited_match'
  | 'expanded_match'
  | 'deadline_alerts'
  | 'scholarship_tools'
  | 'workshops'

export interface BillingPrices {
  student_plan_cents: number
  student_adfree_cents: number
  institution_per_applicant_cents: number
  trial_days: number
  currency: string
}

export interface PaymentMethodInfo {
  id: string
  brand: string | null
  last4: string | null
  exp_month: number | null
  exp_year: number | null
}

export interface BillingStatus {
  enabled: boolean
  mock?: boolean
  /** "mock" | "stripe" — which provider services payments. */
  provider?: string
  /** Stripe publishable key (client-safe), present only when provider="stripe". */
  publishable_key?: string | null
  plan: Plan
  status: string
  trial_ends_at: string | null
  trial_days_left: number | null
  ad_free: boolean
  has_payment_method: boolean
  payment_method?: PaymentMethodInfo | null
  cancel_at_period_end: boolean
  current_period_end: string | null
  entitlements: string[]
  feature_matrix: Record<Plan, Record<string, boolean>>
  prices: BillingPrices
}

export interface BillingEvent {
  id: string
  event_type: string
  amount_cents: number
  currency: string
  status: string
  occurred_at: string | null
  metadata: Record<string, unknown> | null
}

export interface InstitutionUsage {
  enabled: boolean
  unique_applicants: number
  billable_applicants: number
  per_applicant_cents: number
  total_cents: number
  currency: string
  charges: Array<{
    id: string
    student_id: string
    application_id: string | null
    amount_cents: number
    currency: string
    status: string
    charged_at: string | null
    created_at: string | null
  }>
}

export interface AddPaymentMethodInput {
  number?: string
  exp_month?: number
  exp_year?: number
  cvc?: string
  name?: string
  token?: string
}

// Display helpers ------------------------------------------------------------

/** Render integer cents as a currency string, dropping the `.00` on whole amounts. */
export function formatCents(cents: number, currency = 'usd'): string {
  const symbol = currency.toLowerCase() === 'usd' ? '$' : ''
  const whole = cents % 100 === 0
  const amount = (cents / 100).toFixed(whole ? 0 : 2)
  return `${symbol}${amount}`
}

// Human labels for the entitlement features (the "explain everything" grid).
export const FEATURE_LABELS: Record<Feature, string> = {
  profile: 'Portable profile',
  baseline_readiness: 'Baseline readiness',
  limited_match: 'Program matching',
  expanded_match: 'Full matching + reasoning',
  deadline_alerts: 'Real-time deadline alerts',
  scholarship_tools: 'Scholarship & affordability tools',
  workshops: 'Essay, resume & interview workshops',
}

// Plain-English labels for the billing-history ledger.
export const EVENT_LABELS: Record<string, string> = {
  trial_started: 'Free trial started',
  trial_converted: 'Trial converted to Plus',
  subscription_created: 'Subscription started',
  subscription_canceled: 'Subscription canceled',
  payment_succeeded: 'Payment',
  payment_failed: 'Payment failed',
  payment_method_added: 'Card added',
  adfree_enabled: 'Ad-free upgrade added',
  adfree_disabled: 'Ad-free upgrade removed',
  applicant_charged: 'Applicant processed',
}
