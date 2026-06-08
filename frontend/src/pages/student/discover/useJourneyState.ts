/**
 * Derives the guided-journey model (stages + progress + matches unlock) from the
 * existing completion map + handoff verdict — no new backend. Stages: the three
 * Discovery layers (profile → goals → needs). The first layer below the ready
 * threshold is "current"; earlier ones are "done"; later ones "locked".
 */
import { useQuery } from '@tanstack/react-query'
import { getCompletionMap, getHandoffVerdict } from '../../../api/discovery'
import type { CompletionMap, HandoffVerdict } from '../../../types'

export type StageKey = 'profile' | 'goals' | 'needs'
export type StageState = 'done' | 'current' | 'locked'
export interface JourneyStage {
  key: StageKey
  label: string
  state: StageState
  pct: number
}

const READY = 0.5
const LABELS: Record<StageKey, string> = {
  profile: 'About you',
  goals: 'Your goals',
  needs: 'What you need',
}
const ORDER: StageKey[] = ['profile', 'goals', 'needs']

export function deriveStages(c: Partial<CompletionMap> | undefined): JourneyStage[] {
  const pct = (k: StageKey) => Number(c?.[k] ?? 0)
  const firstIncomplete = ORDER.find(k => pct(k) < READY)
  return ORDER.map(key => {
    const p = pct(key)
    const state: StageState = p >= READY ? 'done' : key === firstIncomplete ? 'current' : 'locked'
    return { key, label: LABELS[key], state, pct: p }
  })
}

export function useJourneyState(enabled: boolean) {
  const { data: completion } = useQuery<CompletionMap>({
    queryKey: ['discovery', 'completion'],
    queryFn: getCompletionMap,
    enabled,
  })
  const { data: handoff } = useQuery<HandoffVerdict>({
    queryKey: ['discovery', 'handoff'],
    queryFn: getHandoffVerdict,
    enabled,
  })
  const stages = deriveStages(completion)
  const currentStage = stages.find(s => s.state === 'current') ?? null
  const matchesUnlocked = !!handoff?.should_handoff
  return { stages, currentStage, matchesUnlocked, completion }
}
