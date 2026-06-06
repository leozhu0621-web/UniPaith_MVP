/**
 * Living profile — the durable record Uni builds during the Discover
 * conversation, composed for the in-thread "Noticed" cards (Task 6) and the
 * slide-over drawer (Task 7).
 *
 * Deliberately a thin client-side composition over the existing typed goal /
 * need / identity endpoints (no new backend surface): the narrative is the
 * already-synthesized identity summary, the editable chips map to real goal /
 * need rows, and gaps are computed from what's still empty so Uni can invite
 * the student to go deeper.
 */
import { listGoals, updateGoal } from './goals'
import { getIdentity } from './identity'
import { listNeeds, updateNeed } from './needs'
import type { StudentGoal, StudentNeed } from '../types'

/** One editable chip in the drawer / one inline-editable Noticed item. */
export interface LivingProfileItem {
  kind: 'goal' | 'need'
  id: string
  label: string
  /** Secondary context (goal category / need Maslow level). */
  meta?: string
}

/** A thing Uni hasn't heard about yet — surfaced as a gentle invitation. */
export interface LivingProfileGap {
  key: 'goals' | 'needs' | 'identity'
  /** Completes "Uni could understand you better if we talk about …". */
  invitation: string
  /** Seeded into the conversation when the student accepts the invitation. */
  prompt: string
}

export interface LivingProfile {
  /** Synthesized identity paragraph, or null if not built yet. */
  narrative: string | null
  /** "What lights you up" — identity core values (read-only). */
  lightsUp: string[]
  /** "Where you're headed" — goals (editable). */
  goals: LivingProfileItem[]
  /** "What you need to thrive" — needs (editable). */
  needs: LivingProfileItem[]
  gaps: LivingProfileGap[]
}

const GAP_GOALS: LivingProfileGap = {
  key: 'goals',
  invitation: "what you're hoping to get out of all this",
  prompt: "I'd like to talk about what I'm hoping to get out of college.",
}
const GAP_NEEDS: LivingProfileGap = {
  key: 'needs',
  invitation: 'what you need to feel at home somewhere',
  prompt: 'Can we talk about what I need to feel at home at a school?',
}
const GAP_IDENTITY: LivingProfileGap = {
  key: 'identity',
  invitation: 'what matters most to you',
  prompt: "I'd like to talk about what matters most to me.",
}

export const getLivingProfile = async (): Promise<LivingProfile> => {
  const [goals, needs, identity] = await Promise.all([
    listGoals('active').catch(() => [] as StudentGoal[]),
    listNeeds().catch(() => [] as StudentNeed[]),
    getIdentity().catch(() => null),
  ])
  const gaps: LivingProfileGap[] = []
  if (goals.length === 0) gaps.push(GAP_GOALS)
  if (needs.length === 0) gaps.push(GAP_NEEDS)
  if (!identity?.identity_summary) gaps.push(GAP_IDENTITY)
  return {
    narrative: identity?.identity_summary ?? null,
    lightsUp: (identity?.core_values ?? []).map(v => v.value).filter(Boolean),
    goals: goals.map(g => ({ kind: 'goal', id: g.id, label: g.specific, meta: g.category })),
    needs: needs.map(n => ({ kind: 'need', id: n.id, label: n.signal, meta: n.maslow_level })),
    gaps,
  }
}

/**
 * Update one captured signal in place. Dispatches to the existing typed
 * endpoint so the Noticed card / drawer chip can edit goals and needs through
 * a single uniform call.
 */
export const updateSignal = (ref: {
  kind: 'goal' | 'need'
  id: string
  value: string
}): Promise<StudentGoal | StudentNeed> =>
  ref.kind === 'goal'
    ? updateGoal(ref.id, { specific: ref.value })
    : updateNeed(ref.id, { signal: ref.value })
