/** Post-auth landing paths per Spec/04 §9 and §11. */
export function roleDefaultPath(role: 'student' | 'institution_admin' | string | undefined): string {
  if (role === 'institution_admin') return '/i/dashboard'
  return '/s'
}

/** Safe redirect target from ?next= query param. */
export function resolveNextParam(next: string | null, fallback: string): string {
  if (!next) return fallback
  if (!next.startsWith('/') || next.startsWith('//')) return fallback
  if (next.startsWith('/login') || next.startsWith('/signup')) return fallback
  return next
}

/**
 * The normal (non-onboarding) post-auth destination: honor a safe ?next=,
 * else the role default.
 *
 * Onboarding routing is deliberately NOT a parameter here (the old
 * `onboardingPending` flag was dead — nothing ever passed it). The ONE
 * mechanism (UX overhaul Ship C §3) is fetch-based: after any successful auth,
 * student callers fetch the profile and check
 * `needsOnboarding(role, profile?.onboarding_state)`
 * (pages/student/onboarding/onboarding-state.ts) — true → '/onboarding',
 * false → this function. See LoginPage / AuthCallbackPage; SignupPage routes
 * straight to /onboarding (new accounts always need it).
 */
export function postLoginDestination(
  role: string | undefined,
  searchParams: URLSearchParams,
): string {
  const next = resolveNextParam(searchParams.get('next'), '')
  if (next) return next
  return roleDefaultPath(role)
}
