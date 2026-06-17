import {
  Compass,
  ListChecks,
  Send,
  Scale,
  GraduationCap,
  BookOpen,
  Briefcase,
  FlaskConical,
  Cpu,
  Wrench,
  TrendingUp,
  HeartPulse,
  Palette,
  Music,
  Landmark,
  Gavel,
  School,
  Newspaper,
  Sigma,
  CircuitBoard,
  Leaf,
  Languages,
  Rocket,
  type LucideIcon,
} from 'lucide-react'
import type { OnboardingBudgetBand, OnboardingDegreeLevel, OnboardingStage } from '../../../types'

/**
 * Static option catalogs for the onboarding wizard (UX overhaul Ship C §3).
 * Track keys/labels mirror the authoritative 15-track registry in
 * unipaith-backend services/major_track_catalog.py (Spec 43 §1) — keys must
 * stay byte-identical so the answers fan cleanly into track activation later.
 */

export interface WizardOption<V extends string = string> {
  value: V
  label: string
  icon: LucideIcon
  hint?: string
}

export const STAGE_OPTIONS: WizardOption<OnboardingStage>[] = [
  { value: 'exploring', label: 'Just exploring', icon: Compass, hint: 'Figuring out what fits me' },
  { value: 'building_list', label: 'Building my list', icon: ListChecks, hint: 'Comparing schools and programs' },
  { value: 'ready_to_apply', label: 'Ready to apply', icon: Send, hint: 'Deadlines, essays, requirements' },
  { value: 'deciding_offers', label: 'Deciding offers', icon: Scale, hint: 'Weighing admits in hand' },
]

// The 15 discipline tracks (labels lightly shortened for chip-cards).
export const INTEREST_TRACKS: WizardOption[] = [
  { value: 'cs_data_ai', label: 'Computer Science · Data · AI', icon: Cpu },
  { value: 'engineering', label: 'Engineering', icon: Wrench },
  { value: 'business', label: 'Business · Finance · Marketing', icon: TrendingUp },
  { value: 'health', label: 'Health · Pre-med · Nursing', icon: HeartPulse },
  { value: 'arts_design', label: 'Art · Design · Architecture', icon: Palette },
  { value: 'performing_arts', label: 'Performing Arts', icon: Music },
  { value: 'humanities_social_sciences', label: 'Humanities · Social Sciences', icon: Landmark },
  { value: 'law_policy', label: 'Law · Policy · Intl Relations', icon: Gavel },
  { value: 'education_counseling', label: 'Education · Counseling', icon: School },
  { value: 'journalism_communications', label: 'Journalism · Communications', icon: Newspaper },
  { value: 'math_physics_chemistry_sciences', label: 'Math · Physics · Sciences', icon: Sigma },
  { value: 'comp_engineering_robotics', label: 'Computer Eng · Robotics', icon: CircuitBoard },
  { value: 'environmental_sustainability', label: 'Environment · Sustainability', icon: Leaf },
  { value: 'language_linguistics', label: 'Languages · Linguistics', icon: Languages },
  { value: 'entrepreneurship_product', label: 'Entrepreneurship · Product', icon: Rocket },
]

export const DEGREE_OPTIONS: WizardOption<OnboardingDegreeLevel>[] = [
  { value: 'bachelors', label: "Bachelor's", icon: GraduationCap, hint: 'Undergraduate degree' },
  { value: 'masters', label: "Master's", icon: BookOpen, hint: 'MS · MA · MEng and more' },
  { value: 'mba', label: 'MBA', icon: Briefcase, hint: 'Business school' },
  { value: 'phd', label: 'PhD', icon: FlaskConical, hint: 'Doctoral research' },
]

export const BUDGET_OPTIONS: { value: OnboardingBudgetBand; label: string; hint?: string }[] = [
  { value: 'lt_20k', label: 'Under $20k / year' },
  { value: '20k_40k', label: '$20k – $40k / year' },
  { value: '40k_60k', label: '$40k – $60k / year' },
  { value: '60k_plus', label: '$60k+ / year' },
  { value: 'need_aid', label: "I'll need financial aid", hint: 'Surfaces aid-friendly programs' },
]

export const GEO_OPTIONS: string[] = [
  'United States',
  'United Kingdom',
  'Canada',
  'Europe',
  'Australia & NZ',
  'Asia',
  'Anywhere',
]

/**
 * The next `count` plausible intake terms from `now`, alternating
 * Fall Y → Spring Y+1. This year's Fall stays offered through June; from July
 * on the first plausible intake is next Spring.
 * June 2026 → Fall 2026, Spring 2027, Fall 2027, Spring 2028, Fall 2028, Spring 2029.
 */
export function nextIntakeTerms(count = 6, now = new Date()): string[] {
  const terms: string[] = []
  let fallYear = now.getMonth() < 6 ? now.getFullYear() : now.getFullYear() + 1
  const skipFirstFall = now.getMonth() >= 6 // Jul–Dec: Spring (fallYear) leads
  if (skipFirstFall) terms.push(`Spring ${fallYear}`)
  while (terms.length < count) {
    terms.push(`Fall ${fallYear}`)
    if (terms.length < count) terms.push(`Spring ${fallYear + 1}`)
    fallYear += 1
  }
  return terms.slice(0, count)
}
