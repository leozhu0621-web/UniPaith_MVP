/**
 * Spec/04 — route contract helpers for tests and redirects.
 * Single source for legacy redirect targets (§4.4).
 */

export const STUDENT_LEGACY_REDIRECTS: Record<string, string> = {
  '/s/dashboard': '/s',
  '/s/chat': '/s',
  '/s/discover': '/s/explore',
  '/s/match': '/s',
  '/s/applications': '/s/manage',
  '/s/calendar': '/s/manage?tab=calendar',
  '/s/deadlines': '/s/manage?tab=calendar',
  '/s/messages': '/s/manage?tab=messages',
  '/s/financial-aid': '/s/profile?tab=financial',
  '/s/recommendations': '/s/profile?tab=preparation&section=recommenders',
  '/s/resume-workshop': '/s/manage?tab=workshops',
  '/s/essay-workshop': '/s/manage?tab=workshops',
  '/s/test-scores': '/s/profile?tab=academics',
  '/s/decisions': '/s/manage',
  '/s/intake': '/s',
  '/s/intelligence': '/s',
}

/** Map deprecated profile tab keys to the §4.6 tab structure. */
export const PROFILE_TAB_ALIASES: Record<string, string> = {
  essays: '/s/manage?tab=workshops',
  recommenders: '/s/profile?tab=preparation&section=recommenders',
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
