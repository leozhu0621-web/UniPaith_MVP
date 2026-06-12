/**
 * Spec/04 — route contract helpers for tests and redirects.
 * Single source for legacy redirect targets (§4.4).
 */

export const STUDENT_LEGACY_REDIRECTS: Record<string, string> = {
  // My Space (Spec 2026-06-10 §2): /s/applications, /s/calendar and /s/messages
  // are REAL routes again (rooms), so they no longer appear here. /s/manage is
  // retired — bare hits land on mission control; tab deep links are mapped by
  // MANAGE_TAB_REDIRECTS below (param-preserving, one hop, never chains).
  '/s/manage': '/s/space',
  '/s/dashboard': '/s/space',
  '/s/chat': '/s',
  '/s/discover': '/s/explore',
  '/s/match': '/s',
  '/s/deadlines': '/s/calendar',
  '/s/financial-aid': '/s/applications?tab=costs',
  '/s/recommendations': '/s/prep?tab=recommenders',
  '/s/resume-workshop': '/s/prep?tab=workshops',
  '/s/essay-workshop': '/s/prep?tab=workshops',
  '/s/test-scores': '/s/profile?tab=academics',
  '/s/decisions': '/s/applications',
  '/s/intake': '/s',
  '/s/intelligence': '/s',
  // Discover + Connect merge (Spec 2026-06-12) — Connect lives in the
  // Discover hub now; tab deep links are mapped by POSTS_TAB_REDIRECTS below.
  '/s/posts': '/s/explore?tab=updates',
}

/** /s/posts?tab=… → Discover hub tab targets (App.tsx PostsRedirect contract,
 *  Spec 2026-06-12 — Connect merged into Discover). One hop, never chains. */
export const POSTS_TAB_REDIRECTS: Record<string, string> = {
  updates: '/s/explore?tab=updates',
  events: '/s/explore?tab=events',
  peers: '/s/explore?tab=peers',
}

/** /s/manage?tab=… → My Space room targets (App.tsx ManageRedirect contract). */
export const MANAGE_TAB_REDIRECTS: Record<string, string> = {
  applications: '/s/applications',
  calendar: '/s/calendar',
  messages: '/s/messages',
  prompts: '/s/prep?tab=prompts',
  workshops: '/s/prep?tab=workshops',
}

/**
 * Map deprecated profile tab keys OUT of the profile (Spec 2026-06-10 §5):
 * Preparation and Financial left the record — prep work lives in
 * My Space › Prep, money tools in My Space › Applications › Costs & aid.
 * (?tab=preparation&section=recommenders is special-cased in ProfilePage.)
 */
export const PROFILE_TAB_ALIASES: Record<string, string> = {
  essays: '/s/prep?tab=workshops',
  recommenders: '/s/prep?tab=recommenders',
  // The Preparation cluster is the documents repo — land there directly.
  preparation: '/s/prep?tab=documents',
  financial: '/s/applications?tab=costs',
}

export const PROFILE_TABS_SPEC = [
  'overview',
  'identity',
  'academics',
  'experience',
  'goals',
  'needs',
  'strategy',
  'preferences',
  'timeline',
  'analytics',
  'data',
] as const

export type ProfileTabSpec = (typeof PROFILE_TABS_SPEC)[number]

export function normalizeProfileTab(raw: string | null): ProfileTabSpec {
  if (!raw) return 'overview'
  if (PROFILE_TABS_SPEC.includes(raw as ProfileTabSpec)) return raw as ProfileTabSpec
  return 'overview'
}
