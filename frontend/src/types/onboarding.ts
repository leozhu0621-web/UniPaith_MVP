// AUTO-SPLIT from the former monolithic types/index.ts.
// Domain module — see CONTRIBUTING.md. Edit types here, not in a barrel.
// === ONBOARDING (full-scale wizard — UX overhaul Ship C §3) ===
// Mirrors student_profiles.onboarding_state JSONB. All keys optional — a brand
// new account has NULL; a backend that predates the column omits the field
// entirely (treated as null = needs onboarding, see utils/auth-redirect notes).
export type OnboardingStage = 'exploring' | 'building_list' | 'ready_to_apply' | 'deciding_offers'
export type OnboardingDegreeLevel = 'bachelors' | 'masters' | 'mba' | 'phd'
export type OnboardingBudgetBand = 'lt_20k' | '20k_40k' | '40k_60k' | '60k_plus' | 'need_aid'

export interface OnboardingAnswers {
  stage?: OnboardingStage
  /** Discipline track keys from the 15-track major catalog (Spec 43 §1). */
  interests?: string[]
  degree_level?: OnboardingDegreeLevel
  /** e.g. "Fall 2027" */
  intake_term?: string
  budget_band?: OnboardingBudgetBand | null
  geos?: string[]
}

export interface OnboardingState {
  answers?: OnboardingAnswers
  last_step?: number
  completed_at?: string | null
  dismissed_at?: string | null
}
