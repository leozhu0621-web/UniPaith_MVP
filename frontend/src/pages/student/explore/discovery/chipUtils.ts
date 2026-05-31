// Spec 10 — constraint-chip encode/decode + display helpers (pure functions).
import type { ConstraintCategory, ConstraintChip } from '../../../../types/search'
import { CATEGORY_LABELS } from './constants'

export const makeChipId = (category: string, value: string): string =>
  `${category}:${value}`.toLowerCase()

export const categoryLabel = (category: ConstraintCategory): string =>
  CATEGORY_LABELS[category] ?? category

const VALID_CATEGORIES = new Set<string>(Object.keys(CATEGORY_LABELS))

/** Parse the URL `chips` param (JSON) into a validated chip list. Bad input
 *  yields an empty list rather than throwing — deep links must stay robust. */
export function parseChipsParam(raw: string | null): ConstraintChip[] {
  if (!raw) return []
  try {
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    const out: ConstraintChip[] = []
    for (const item of parsed) {
      if (!item || typeof item !== 'object') continue
      const category = String(item.category || '')
      const value = String(item.value || '')
      if (!VALID_CATEGORIES.has(category) || !value) continue
      out.push({
        id: item.id || makeChipId(category, value),
        category: category as ConstraintCategory,
        value,
        display: String(item.display || value),
        confidence: typeof item.confidence === 'number' ? item.confidence : 100,
        user_confirmed: Boolean(item.user_confirmed),
      })
    }
    return out
  } catch {
    return []
  }
}

export const encodeChipsParam = (chips: ConstraintChip[]): string => JSON.stringify(chips)

/** Ensure a chip has an id (deterministic on category+value). */
export const withChipId = (chip: ConstraintChip): ConstraintChip => ({
  ...chip,
  id: chip.id || makeChipId(chip.category, chip.value),
})

// ── Numeric range encode/decode (budget $, duration months) ──────────────────

export interface NumRange {
  min?: number
  max?: number
}

export function decodeRange(value: string): NumRange {
  const v = (value || '').replace(/[,$\s]/g, '')
  let m = v.match(/^<=?(\d+)$/)
  if (m) return { max: Number(m[1]) }
  m = v.match(/^>=?(\d+)$/)
  if (m) return { min: Number(m[1]) }
  m = v.match(/^(\d+)[-–](\d+)$/)
  if (m) {
    const a = Number(m[1])
    const b = Number(m[2])
    return { min: Math.min(a, b), max: Math.max(a, b) }
  }
  m = v.match(/^(\d+)$/)
  if (m) return { max: Number(m[1]) }
  return {}
}

export function encodeRange({ min, max }: NumRange): string {
  if (min != null && max != null) return `${min}-${max}`
  if (max != null) return `<=${max}`
  if (min != null) return `>=${min}`
  return ''
}

const dollars = (n: number): string =>
  n >= 1000 && n % 1000 === 0 ? `$${n / 1000}k` : `$${n.toLocaleString()}`

export function formatBudgetDisplay({ min, max }: NumRange): string {
  if (min != null && max != null) return `${dollars(min)}–${dollars(max)}/yr`
  if (max != null) return `≤ ${dollars(max)}/yr`
  if (min != null) return `≥ ${dollars(min)}/yr`
  return 'Budget'
}

const months = (m: number): string => (m % 12 === 0 ? `${m / 12} yr` : `${m} mo`)

export function formatDurationDisplay({ min, max }: NumRange): string {
  if (min != null && max != null && min !== max) return `${months(min)}–${months(max)}`
  if (max != null) return `≤ ${months(max)}`
  if (min != null) return `≥ ${months(min)}`
  return 'Duration'
}
