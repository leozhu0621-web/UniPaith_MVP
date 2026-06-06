import type { MatchBand, MatchResultDual, ProgramSummary, SavedProgram } from '../../../types'

export function programSummaryOf(sp: SavedProgram): ProgramSummary {
  const p = sp.program
  if (p) return p
  return {
    id: sp.program_id,
    institution_id: '',
    program_name: sp.program_name ?? 'Program',
    degree_type: 'masters',
    institution_name: sp.institution_name ?? '',
    institution_country: '',
  } as ProgramSummary
}

/** Build a match-context payload for MatchCard when dual scores exist. */
export function matchDualOf(sp: SavedProgram): MatchResultDual | null {
  if (sp.fitness_score == null && sp.confidence_score == null) return null
  const p = sp.program
  const fitness = sp.fitness_score ?? 0
  const confidence = sp.confidence_score ?? 0
  return {
    id: sp.id,
    student_id: '',
    program_id: sp.program_id,
    fitness_score: String(fitness),
    confidence_score: String(confidence),
    fitness_breakdown: null,
    confidence_breakdown: null,
    rationale_text: null,
    rationale_generated_at: null,
    strategy_version_id: null,
    match_score: String(fitness),
    score_breakdown: null,
    match_tier: null,
    reasoning_text: null,
    model_version: null,
    computed_at: sp.added_at,
    is_stale: false,
    program_name: p?.program_name ?? sp.program_name,
    institution_name: p?.institution_name ?? sp.institution_name,
    degree_type: p?.degree_type ?? undefined,
    tuition: p?.tuition ?? undefined,
    acceptance_rate: p?.acceptance_rate ?? undefined,
    band_label: (sp.band_label ?? undefined) as MatchBand | undefined,
    probability_bands: null,
  }
}

export type SortKey = 'fitness_score' | 'date_added' | 'deadline'

export function sortSavedPrograms(list: SavedProgram[], sortKey: SortKey): SavedProgram[] {
  return [...list].sort((a, b) => {
    if (sortKey === 'fitness_score') {
      const sa = a.fitness_score ?? -1
      const sb = b.fitness_score ?? -1
      return sb - sa
    }
    if (sortKey === 'deadline') {
      const da = a.program?.application_deadline ?? '9999'
      const db = b.program?.application_deadline ?? '9999'
      return da.localeCompare(db)
    }
    return new Date(b.added_at).getTime() - new Date(a.added_at).getTime()
  })
}
