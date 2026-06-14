export type StageKey = 'discover' | 'match' | 'apply' | 'decide'

export const STAGES: { key: StageKey; label: string; to: string }[] = [
  { key: 'discover', label: 'Discover', to: '/s' },
  { key: 'match', label: 'Match', to: '/s/explore' },
  { key: 'apply', label: 'Apply', to: '/s/applications' },
  { key: 'decide', label: 'Decide', to: '/s/applications?tab=offers' },
]

export interface StageInputs {
  savedCount: number
  appCount: number
  hasDecision: boolean
  hasOffer: boolean
}

/** Furthest-reached stage from data the home already fetches (Spec 2026-06-14
 *  §Modules.2b). Match is inferred from saved programs (the home fetches saved
 *  but not matches), so no extra query is added. */
export function deriveStage({ savedCount, appCount, hasDecision, hasOffer }: StageInputs): StageKey {
  if (hasDecision || hasOffer) return 'decide'
  if (appCount > 0) return 'apply'
  if (savedCount > 0) return 'match'
  return 'discover'
}

export function stageIndex(key: StageKey): number {
  return STAGES.findIndex(s => s.key === key)
}
