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

export function postLoginDestination(
  role: string | undefined,
  searchParams: URLSearchParams,
  onboardingPending = false,
): string {
  const next = resolveNextParam(searchParams.get('next'), '')
  if (next) return next
  if (role === 'student' && onboardingPending) return '/onboarding'
  return roleDefaultPath(role)
}
