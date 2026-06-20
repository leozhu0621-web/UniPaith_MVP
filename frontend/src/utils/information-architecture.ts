/**
 * Spec/04 — route contract helpers for tests and redirects.
 * Single source for legacy redirect targets (§4.4).
 */

export const STUDENT_LEGACY_REDIRECTS: Record<string, string> = {
  '/s/dashboard': '/s/space',
  '/s/chat': '/s',
  '/s/discover': '/s/explore',
  '/s/match': '/s',
  '/s/manage': '/s/space',
  '/s/deadlines': '/s/calendar',
  '/s/financial-aid': '/s/profile?tab=financial',
  '/s/recommendations': '/s/prep?tab=recommenders',
  '/s/resume-workshop': '/s/prep?tab=workshops',
  '/s/essay-workshop': '/s/prep?tab=workshops',
  '/s/prompts': '/s/prep?tab=prompts',
  '/s/test-scores': '/s/profile?tab=academics',
  '/s/decisions': '/s/applications?tab=offers',
  '/s/intake': '/s',
  '/s/intelligence': '/s',
}

/** Map deprecated profile tab keys to the §4.6 tab structure. */
export const PROFILE_TAB_ALIASES: Record<string, string> = {
  essays: '/s/prep?tab=workshops',
  recommenders: '/s/prep?tab=recommenders',
}

export const PROFILE_TABS_SPEC = [
  'overview',
  'identity',
  'academics',
  'experience',
  'goals',
  'needs',
  'strategy',
  'preparation',
  'preferences',
  'financial',
  'timeline',
  'analytics',
  'data',
] as const

export type ProfileTabSpec = (typeof PROFILE_TABS_SPEC)[number]

export function normalizeProfileTab(raw: string | null): ProfileTabSpec {
  if (!raw) return 'overview'
  if (raw === 'recommenders') return 'preparation'
  if (PROFILE_TABS_SPEC.includes(raw as ProfileTabSpec)) return raw as ProfileTabSpec
  return 'overview'
}
