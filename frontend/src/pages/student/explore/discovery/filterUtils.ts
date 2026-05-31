// Spec 10 §5 — panel filter encode/decode + helpers (pure functions).
import type { SearchFilters } from '../../../../types/search'

const STRING_KEYS = ['campus_setting', 'program_name', 'country', 'region', 'city'] as const
const NUMBER_KEYS = [
  'min_tuition',
  'max_tuition',
  'min_duration_months',
  'max_duration_months',
  'min_acceptance_rate',
  'max_acceptance_rate',
  'start_year',
  'min_median_salary',
  'min_employment_rate',
  'max_payback_months',
] as const
const LIST_KEYS = ['degree_types', 'delivery_formats'] as const

export const EMPTY_FILTERS: SearchFilters = {}

/** Parse the URL `filters` param (JSON) into a validated, normalized object.
 *  Bad input yields {} rather than throwing so deep links stay robust. */
export function parseFiltersParam(raw: string | null): SearchFilters {
  if (!raw) return {}
  try {
    const parsed = JSON.parse(raw)
    if (!parsed || typeof parsed !== 'object') return {}
    const out: SearchFilters = {}
    for (const k of STRING_KEYS) {
      const v = parsed[k]
      if (typeof v === 'string' && v.trim()) out[k] = v.trim()
    }
    for (const k of NUMBER_KEYS) {
      const v = parsed[k]
      if (typeof v === 'number' && Number.isFinite(v)) out[k] = v
    }
    for (const k of LIST_KEYS) {
      const v = parsed[k]
      if (Array.isArray(v)) {
        const list = v.filter((x): x is string => typeof x === 'string' && !!x)
        if (list.length) out[k] = list
      }
    }
    return out
  } catch {
    return {}
  }
}

/** Drop empty values so the URL/payload only carries meaningful filters. */
export function normalizeFilters(f: SearchFilters): SearchFilters {
  const out: SearchFilters = {}
  for (const k of STRING_KEYS) {
    const v = f[k]
    if (typeof v === 'string' && v.trim()) out[k] = v.trim()
  }
  for (const k of NUMBER_KEYS) {
    const v = f[k]
    if (typeof v === 'number' && Number.isFinite(v)) out[k] = v
  }
  for (const k of LIST_KEYS) {
    const v = f[k]
    if (Array.isArray(v) && v.length) out[k] = v
  }
  return out
}

export const encodeFiltersParam = (f: SearchFilters): string => JSON.stringify(normalizeFilters(f))

/** Count of distinct active facets — drives the accent count badge (§13).
 *  A min/max pair on the same facet counts once. */
export function countActiveFilters(f: SearchFilters): number {
  const n = normalizeFilters(f)
  let count = 0
  if (n.campus_setting) count++
  if (n.program_name) count++
  if (n.country || n.region || n.city) count++
  if (n.degree_types?.length) count++
  if (n.delivery_formats?.length) count++
  if (n.min_tuition != null || n.max_tuition != null) count++
  if (n.min_duration_months != null || n.max_duration_months != null) count++
  if (n.min_acceptance_rate != null || n.max_acceptance_rate != null) count++
  if (n.start_year != null) count++
  if (n.min_median_salary != null) count++
  if (n.min_employment_rate != null) count++
  if (n.max_payback_months != null) count++
  return count
}

export const hasActiveFilters = (f: SearchFilters): boolean => countActiveFilters(f) > 0

/** Selectivity band ⇄ acceptance-rate range (0–1). Mirrors the backend
 *  `_SELECTIVITY_BANDS` so the panel and the chip agree. */
export const SELECTIVITY_BANDS: Record<string, { min?: number; max?: number }> = {
  low: { min: 0.6 },
  medium: { min: 0.3, max: 0.6 },
  high: { min: 0.1, max: 0.3 },
  very_high: { max: 0.1 },
}

export function selectivityFromRange(min?: number | null, max?: number | null): string {
  for (const [band, range] of Object.entries(SELECTIVITY_BANDS)) {
    if ((range.min ?? null) === (min ?? null) && (range.max ?? null) === (max ?? null)) return band
  }
  return ''
}
