import type { ElementImportance, IssueSeverity, WorkshopFeedbackRun } from '../../../types'

/** severity → Badge variant (Spec/02-design-system.md §11 alert colors). */
export const SEVERITY_VARIANT: Record<IssueSeverity, 'danger' | 'warning' | 'neutral'> = {
  major: 'danger',
  moderate: 'warning',
  minor: 'neutral',
}

/** importance → Badge variant. */
export const IMPORTANCE_VARIANT: Record<ElementImportance, 'danger' | 'warning' | 'neutral'> = {
  required: 'danger',
  should_have: 'warning',
  nice_to_have: 'neutral',
}

const prettify = (k: string) => k.replace(/_/g, ' ')

/**
 * Per-program readiness summary in student language (Spec/14-workshops.md §6).
 *
 * Derived client-side from the run's rubric + missing elements. This is pure
 * feedback synthesis — it never generates any part of the student's artifact,
 * so it stays inside the feedback-only contract. Returns null when there's
 * nothing meaningful to say.
 */
export function readinessSummary(
  run: WorkshopFeedbackRun,
  programName: string,
): string | null {
  const requiredMissing = (run.missing_elements ?? []).filter(m => m.importance === 'required')

  if (run.domain === 'test') {
    const target = run.rubric_scores?.target_score
    const gap = run.rubric_scores?.gap
    if (typeof gap === 'number') {
      if (gap <= 0) {
        return `For ${programName}: you're already at or above target — keep it consistent.`
      }
      const band = gap <= 50 ? 'a small' : gap <= 150 ? 'a moderate' : 'a large'
      const targetStr = typeof target === 'number' ? ` of ${target}` : ''
      return `For ${programName}: ${band} gap to your target${targetStr} — plan prep accordingly.`
    }
    return `For ${programName}: add your current and target scores for a tailored gap plan.`
  }

  const scored = Object.entries(run.rubric_scores ?? {}).filter(
    ([, v]) => typeof v === 'number' && v >= 0 && v <= 5,
  )

  if (scored.length === 0) {
    return requiredMissing.length
      ? `For ${programName}: ${requiredMissing.length} required element${requiredMissing.length > 1 ? 's' : ''} still missing.`
      : null
  }

  const best = scored.reduce((a, b) => (b[1] > a[1] ? b : a))
  const worst = scored.reduce((a, b) => (b[1] < a[1] ? b : a))

  const parts: string[] = [`strongest on ${prettify(best[0])}`]
  if (worst[0] !== best[0]) parts.push(`focus on ${prettify(worst[0])}`)
  if (requiredMissing.length) {
    parts.push(
      `${requiredMissing.length} required element${requiredMissing.length > 1 ? 's' : ''} to add`,
    )
  }

  return `For ${programName}: ${parts.join(' · ')}.`
}
