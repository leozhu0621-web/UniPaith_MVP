// Spec 10 §8 — the five side-by-side compare dimensions + value formatters.
// Shared by CompareTray; pure data so it's trivially testable.
import { DEGREE_LABELS } from '../../utils/constants'

export interface CompareProgram {
  id: string
  program_name: string
  institution_name?: string | null
  institution_country?: string | null
  institution_city?: string | null
  campus_setting?: string | null
  degree_type?: string | null
  department?: string | null
  duration_months?: number | null
  tuition?: number | null
  delivery_format?: string | null
  acceptance_rate?: number | null
  application_deadline?: string | null
  median_salary?: number | null
  employment_rate?: number | null
  payback_months?: number | null
  fitness_score?: number | null
  confidence_score?: number | null
}

const dash = '—'

const money = (n?: number | null): string =>
  n == null ? dash : `$${Math.round(n).toLocaleString()}`

const pct = (n?: number | null): string => (n == null ? dash : `${Math.round(n * 100)}%`)

const titleCase = (s?: string | null): string =>
  s ? s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) : dash

const duration = (months?: number | null): string => {
  if (!months) return dash
  if (months < 12) return `${months} mo`
  const years = months / 12
  return Number.isInteger(years) ? `${years} yr${years > 1 ? 's' : ''}` : `${years.toFixed(1)} yrs`
}

const FORMAT_LABELS: Record<string, string> = {
  on_campus: 'On campus',
  in_person: 'In-person',
  online: 'Online',
  hybrid: 'Hybrid',
}
const formatLabel = (f?: string | null): string => (f ? FORMAT_LABELS[f] ?? titleCase(f) : dash)

const degreeLabel = (d?: string | null): string => (d ? DEGREE_LABELS[d] ?? titleCase(d) : dash)

const payback = (months?: number | null): string => (months == null ? dash : `${months} mo`)

export interface CompareRow {
  label: string
  get: (p: CompareProgram) => string
  /** Raw magnitude for a StatBar. Present only on numeric rows; null when a
   *  program has no value. Non-numeric rows (city, format…) omit it entirely. */
  num?: (p: CompareProgram) => number | null
  /** Whether the highest value wins the column highlight. Set only where "more
   *  is plainly better" (fit, salary…). Lower-better/ambiguous rows leave it
   *  unset — they show magnitude bars but crown no winner. */
  higherIsBetter?: boolean
}

export interface CompareDimension {
  title: string
  rows: CompareRow[]
}

export const COMPARE_DIMENSIONS: CompareDimension[] = [
  {
    title: 'Structure & format',
    rows: [
      { label: 'Degree', get: p => degreeLabel(p.degree_type) },
      { label: 'Field', get: p => p.department || dash },
      { label: 'Duration', get: p => duration(p.duration_months), num: p => p.duration_months ?? null },
      { label: 'Format', get: p => formatLabel(p.delivery_format) },
    ],
  },
  {
    title: 'Location & setting',
    rows: [
      { label: 'City', get: p => p.institution_city || dash },
      { label: 'Country', get: p => p.institution_country || dash },
      { label: 'Campus setting', get: p => titleCase(p.campus_setting) },
    ],
  },
  {
    title: 'Cost & affordability',
    rows: [
      { label: 'Tuition / yr', get: p => money(p.tuition), num: p => p.tuition ?? null },
      { label: 'Payback period', get: p => payback(p.payback_months), num: p => p.payback_months ?? null },
    ],
  },
  {
    title: 'Access & competitiveness',
    rows: [
      { label: 'Acceptance rate', get: p => pct(p.acceptance_rate), num: p => p.acceptance_rate ?? null },
      { label: 'Fit', get: p => pct(p.fitness_score), num: p => p.fitness_score ?? null, higherIsBetter: true },
      { label: 'Confidence', get: p => pct(p.confidence_score), num: p => p.confidence_score ?? null, higherIsBetter: true },
    ],
  },
  {
    title: 'Outcomes & employer signals',
    rows: [
      { label: 'Median salary', get: p => money(p.median_salary), num: p => p.median_salary ?? null, higherIsBetter: true },
      { label: 'Employment rate', get: p => pct(p.employment_rate), num: p => p.employment_rate ?? null, higherIsBetter: true },
    ],
  },
]
