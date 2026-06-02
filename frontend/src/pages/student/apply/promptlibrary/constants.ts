// Spec 42 — Prompt Library label maps + the client-side STAR preview heuristic
// (a compact mirror of ai/prompt_coach.detect_star; the server flags are
// authoritative, this just lights the chips live as the student types).

import type { DraftStatus } from '../../../../types/promptLibrary'

export const INTENT_LABELS: Record<string, string> = {
  leadership: 'Leadership',
  conflict: 'Conflict',
  failure: 'Failure & growth',
  impact: 'Impact',
  ethics: 'Ethics & integrity',
  learning: 'Learning',
  motivation: 'Motivation',
  fit: 'Fit',
  vision: 'Vision',
  curiosity: 'Curiosity',
  resilience: 'Resilience',
  service: 'Service',
  teamwork: 'Teamwork',
  communication: 'Communication',
  identity: 'Identity',
}

export const CHANNEL_LABELS: Record<string, string> = {
  interview: 'Interview',
  essay: 'Essay',
  short_answer: 'Short answer',
  video: 'Video',
}

export const COMPETENCY_LABELS: Record<string, string> = {
  leadership: 'Leadership',
  teamwork: 'Teamwork',
  impact: 'Impact',
  resilience: 'Resilience',
  creativity: 'Creativity',
  analytical: 'Analytical',
  communication: 'Communication',
  initiative: 'Initiative',
}

export const COMPETENCIES = Object.keys(COMPETENCY_LABELS)

export const DRAFT_META: Record<DraftStatus, { label: string; variant: 'neutral' | 'info' | 'success' }> = {
  none: { label: 'Not started', variant: 'neutral' },
  draft: { label: 'Draft', variant: 'info' },
  revised: { label: 'Revised', variant: 'info' },
  final: { label: 'Final', variant: 'success' },
}

export const ROLE_TYPES = ['leader', 'contributor', 'founder', 'observer']
export const STAKEHOLDER_TYPES = ['peers', 'authority', 'clients', 'public', 'self']
export const CONFLICT_TYPES = ['interpersonal', 'resource', 'ethical', 'technical', 'time', 'none']
export const CONTEXT_TAGS = ['school', 'work', 'personal', 'research', 'community']

export const STAR_ELEMENTS: { key: StarKey; label: string; letter: string }[] = [
  { key: 'situation', label: 'Situation', letter: 'S' },
  { key: 'task', label: 'Task', letter: 'T' },
  { key: 'action', label: 'Action', letter: 'A' },
  { key: 'result', label: 'Result', letter: 'R' },
  { key: 'reflection', label: 'Reflection', letter: '+' },
]

export type StarKey = 'situation' | 'task' | 'action' | 'result' | 'reflection'

const STAR_CUES: Record<StarKey, string[]> = {
  situation: ['when ', 'during ', 'at the time', 'we were', 'there was', 'the situation', 'faced with', 'in my role', 'initially', 'while '],
  task: ['needed to', 'my goal', 'my task', 'responsible for', 'had to', 'the challenge was', 'the problem was', 'the goal was', 'was tasked', 'required to', 'asked me to'],
  action: ['so i ', 'i led', 'i built', 'i created', 'i organized', 'i decided', 'i implemented', 'i proposed', 'i reached out', 'i started', 'i designed', 'i developed', 'i launched', 'i resolved', 'i wrote', 'my approach', 'to address', 'i worked', 'i took'],
  result: ['as a result', 'resulted in', 'achieved', 'increased', 'decreased', 'reduced', 'improved', 'grew', 'we won', 'ultimately', 'in the end', 'the outcome', 'led to', 'raised', 'saved', 'delivered', 'completed'],
  reflection: ['i learned', 'in retrospect', 'looking back', 'this taught me', 'i realized', 'next time', 'takeaway', 'going forward', 'reflecting', 'this experience', 'i understood'],
}

const FIRST_PERSON_ACTION = /\bi\s+[a-z]+ed\b/i

/** Client-side STAR preview — mirrors the backend heuristic for live chips. */
export function previewStar(text: string): Record<StarKey, boolean> {
  const low = (text || '').toLowerCase()
  const out = {
    situation: false,
    task: false,
    action: false,
    result: false,
    reflection: false,
  } as Record<StarKey, boolean>
  if (!low.trim()) return out
  ;(Object.keys(STAR_CUES) as StarKey[]).forEach(k => {
    out[k] = STAR_CUES[k].some(cue => low.includes(cue))
  })
  if (!out.action && FIRST_PERSON_ACTION.test(text)) out.action = true
  return out
}

export function wordCount(text: string | null | undefined): number {
  return (text || '').trim() ? (text || '').trim().split(/\s+/).length : 0
}

export function starCount(flags: Record<StarKey, boolean>): number {
  return Object.values(flags).filter(Boolean).length
}
