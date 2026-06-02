import apiClient from './client'

// Billing (Spec 07 §4, 21 §2.7/§3.6).

export type SubscriptionStatus = 'trialing' | 'active' | 'canceled' | 'expired'

export interface InvoiceItem {
  id: string
  date: string
  amount_usd: number
  status: 'paid' | 'due' | 'upcoming'
  description: string
}

export interface StudentBilling {
  status: SubscriptionStatus
  plan_price_usd: number
  ad_free: boolean
  ad_free_addon_usd: number
  monthly_total_usd: number
  trial_ends_at: string | null
  trial_days_left: number | null
  current_period_end: string | null
  cancel_at_period_end: boolean
  has_payment_method: boolean
  payment_method_brand: string | null
  payment_method_last4: string | null
  is_premium: boolean
  paywall_enforced: boolean
  invoices: InvoiceItem[]
  /** "mock" | "stripe" — which provider services payments. */
  provider: string
  /** Stripe publishable key (client-safe); present only when provider="stripe". */
  publishable_key: string | null
}

export interface InstitutionBilling {
  per_applicant_usd: number
  cycle_label: string
  cycle_start: string
  cycle_end: string
  applicants_processed: number
  current_charge_usd: number
  has_payment_method: boolean
  payment_method_brand: string | null
  payment_method_last4: string | null
  invoices: InvoiceItem[]
}

export const getStudentBilling = (): Promise<StudentBilling> =>
  apiClient.get('/students/me/billing').then(r => r.data)

export const upgradeStudentBilling = (paymentMethodToken?: string): Promise<StudentBilling> =>
  apiClient
    .post(
      '/students/me/billing/upgrade',
      paymentMethodToken ? { payment_method_token: paymentMethodToken } : {}
    )
    .then(r => r.data)

export const setAdFree = (enabled: boolean): Promise<StudentBilling> =>
  apiClient.post('/students/me/billing/ad-free', { enabled }).then(r => r.data)

export const cancelStudentBilling = (): Promise<StudentBilling> =>
  apiClient.post('/students/me/billing/cancel').then(r => r.data)

export const resumeStudentBilling = (): Promise<StudentBilling> =>
  apiClient.post('/students/me/billing/resume').then(r => r.data)

export const getInstitutionBilling = (): Promise<InstitutionBilling> =>
  apiClient.get('/institutions/me/billing').then(r => r.data)
