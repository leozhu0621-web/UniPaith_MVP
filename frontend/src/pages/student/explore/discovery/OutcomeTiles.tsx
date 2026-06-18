// Outcome-first discovery (Discover review 2026-06-14 #2). The empty-state genre
// tiles browse by SUBJECT; these browse by OUTCOME (Niche "after graduation" /
// LinkedIn "where graduates work"). Each tile writes the existing ROI FILTERS +
// a sort — so only programs with real outcome data surface (no fabrication).
import { TrendingUp, Briefcase, PiggyBank } from 'lucide-react'
import type { SearchFilters, SortOption } from '../../../../types/search'

export interface OutcomePreset {
  key: string
  label: string
  icon: typeof TrendingUp
  filters: SearchFilters
  sort: SortOption
}

// Floors are deliberately modest so the tiles surface a useful set, not an empty
// one; the sort then orders by the outcome within that floor.
export const OUTCOME_PRESETS: OutcomePreset[] = [
  { key: 'earning', label: 'High earning potential', icon: TrendingUp, filters: { min_median_salary: 60000 }, sort: 'salary_desc' },
  { key: 'placement', label: 'Strong job placement', icon: Briefcase, filters: { min_employment_rate: 0.8 }, sort: 'employment_desc' },
  { key: 'value', label: 'Low tuition, high salary', icon: PiggyBank, filters: { max_tuition: 20000, min_median_salary: 60000 }, sort: 'salary_desc' },
]

interface Props {
  onPick: (preset: OutcomePreset) => void
}

export default function OutcomeTiles({ onPick }: Props) {
  return (
    <div data-testid="outcome-tiles" className="mb-4">
      <p className="text-eyebrow uppercase text-muted-foreground font-semibold mb-2">Browse by outcome</p>
      <div className="flex flex-wrap gap-2">
        {OUTCOME_PRESETS.map(t => (
          <button
            key={t.key}
            type="button"
            onClick={() => onPick(t)}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-muted border border-border text-sm text-foreground hover:border-secondary/50 hover:bg-muted/60 transition-colors"
          >
            <t.icon size={14} className="text-secondary" aria-hidden />
            {t.label}
          </button>
        ))}
      </div>
    </div>
  )
}
