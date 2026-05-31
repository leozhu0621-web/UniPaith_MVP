// Spec 07 (Product Context §4) — monetization / billing types.

export type SubscriptionStatus = 'trialing' | 'active' | 'canceled' | 'expired'
export type SubscriptionPlan = 'free' | 'pro'

export interface Subscription {
  status: SubscriptionStatus
  plan: SubscriptionPlan
  effective_plan: SubscriptionPlan
  ad_free: boolean
  is_trialing: boolean
  is_active: boolean
  has_pro_access: boolean
  trial_ends_at: string | null
  current_period_end: string | null
  days_left_in_trial: number | null
  card_brand: string | null
  card_last4: string | null
  entitlements: string[]
}

export interface SubscribePayload {
  card_brand?: string
  card_last4: string
  ad_free?: boolean
}

export interface PlanFeature {
  label: string
  free: boolean
  pro: boolean
}

export interface StudentPlanCatalog {
  id: string
  name: string
  tagline: string
  price_monthly: number
  currency: string
  trial_days: number
  ad_free_addon_monthly: number
}

export interface InstitutionPlanCatalog {
  id: string
  name: string
  tagline: string
  price_per_applicant: number
  currency: string
  billing_model: string
}

export interface PlanCatalog {
  student: StudentPlanCatalog
  institution: InstitutionPlanCatalog
  features: PlanFeature[]
}

// Pro feature keys (must match services/subscription_service.py PRO_FEATURES).
export const FEATURE = {
  expandedMatching: 'expanded_matching',
  deadlineAlerts: 'deadline_alerts',
  scholarshipTools: 'scholarship_tools',
  writingWorkflows: 'writing_workflows',
  prioritySupport: 'priority_support',
} as const
