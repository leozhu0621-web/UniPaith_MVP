import type { OnboardingAnswers, OnboardingState } from '../../../types'

/**
 * Onboarding needs-rule + local draft persistence (UX overhaul Ship C §3).
 *
 * THE one entry-routing mechanism (replaces both the 60-second account-age
 * heuristic and the dead `onboardingPending` param in utils/auth-redirect.ts):
 * after ANY successful auth, student callers fetch the profile and ask
 * `needsOnboarding(role, profile?.onboarding_state)` — true routes to
 * /onboarding, false to the normal destination.
 *
 * The local draft (`up-onboarding-draft`) exists for deploy ordering: the
 * frontend can land before the backend grows the column, so every PATCH
 * failure falls back to localStorage and the needs-rule honors local
 * completed/dismissed stamps. Once the server answers, the server wins.
 */

export const ONBOARDING_DRAFT_KEY = 'up-onboarding-draft'

export function readLocalDraft(): OnboardingState | null {
  try {
    const raw = localStorage.getItem(ONBOARDING_DRAFT_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    return parsed && typeof parsed === 'object' ? (parsed as OnboardingState) : null
  } catch {
    return null
  }
}

/** Key-wise merge of an answers patch + step/stamps into the stored draft. */
export function writeLocalDraft(patch: {
  answers?: Partial<OnboardingAnswers>
  last_step?: number
  completed?: boolean
  dismissed?: boolean
}): OnboardingState {
  const prev = readLocalDraft() ?? {}
  const next: OnboardingState = {
    ...prev,
    answers: { ...prev.answers, ...patch.answers },
    ...(patch.last_step !== undefined ? { last_step: patch.last_step } : {}),
    ...(patch.completed ? { completed_at: prev.completed_at ?? new Date().toISOString() } : {}),
    ...(patch.dismissed ? { dismissed_at: prev.dismissed_at ?? new Date().toISOString() } : {}),
  }
  try {
    localStorage.setItem(ONBOARDING_DRAFT_KEY, JSON.stringify(next))
  } catch {
    /* storage full / blocked — draft is best-effort */
  }
  return next
}

export function clearLocalDraft(): void {
  try {
    localStorage.removeItem(ONBOARDING_DRAFT_KEY)
  } catch {
    /* ignore */
  }
}

/**
 * Resume state = server state (authoritative) overlaid with any local draft —
 * the draft only exists when a PATCH failed, so where both have a value the
 * draft is the newer write and wins key-wise.
 */
export function mergeWithLocalDraft(server: OnboardingState | null | undefined): OnboardingState {
  const draft = readLocalDraft()
  if (!draft) return server ?? {}
  if (!server) return draft
  return {
    ...server,
    ...draft,
    answers: { ...server.answers, ...draft.answers },
    completed_at: server.completed_at ?? draft.completed_at ?? null,
    dismissed_at: server.dismissed_at ?? draft.dismissed_at ?? null,
  }
}

/**
 * Contract §4: role==student AND onboarding_state?.completed_at==null AND
 * dismissed_at==null. A missing field (backend predates the column) counts as
 * null = needs onboarding; local completed/dismissed stamps count so a
 * frontend-first deploy never loops users back into the wizard.
 */
export function needsOnboarding(
  role: string | undefined,
  serverState: OnboardingState | null | undefined,
): boolean {
  if (role !== 'student') return false
  const state = mergeWithLocalDraft(serverState)
  return state.completed_at == null && state.dismissed_at == null
}
