// Spec 28 §11 / 02-design-system §14 — chart palette + shared formatters.
// Series order: cobalt → gold → success → warning → muted. Never >5 colors.
//
// Colors are CSS-var-backed so Recharts re-themes in dark mode: SVG `fill` /
// `stop-color` resolve `var()` against the live theme at paint time. cobalt and
// gold track --secondary / --primary (which shift in `.dark`); green/amber are
// semantic decision colors that intentionally read the same across themes; muted
// follows --muted-foreground so the catch-all stays legible on dark surfaces.
export const CHART = {
  cobalt: 'hsl(var(--secondary))',
  gold: 'hsl(var(--primary))',
  green: '#1F6B2E',
  amber: '#B8741D',
  muted: 'hsl(var(--muted-foreground))',
} as const

// Institution categorical series — cobalt lead, no gold (matches the recruitment
// palette + its brand test). Gold stays reserved for earned student-side beats.
export const SERIES = [CHART.cobalt, CHART.green, CHART.amber, CHART.muted]

// §14 — tooltip uses popover styling (theme-aware via CSS vars).
export const TOOLTIP_STYLE = {
  background: 'hsl(var(--popover))',
  border: '1px solid hsl(var(--border))',
  borderRadius: 12,
  fontSize: 12,
  color: 'hsl(var(--foreground))',
  boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
} as const

export const AXIS_TICK = { fontSize: 11, fill: 'hsl(var(--muted-foreground))' } as const
export const GRID_STROKE = 'hsl(var(--border))'

export const TIME_WINDOWS = [
  { value: '7d', label: 'Last 7 days' },
  { value: '30d', label: 'Last 30 days' },
  { value: '90d', label: 'Last 90 days' },
  { value: 'yoy', label: 'Year over year' },
  { value: 'all', label: 'All time' },
]

const PRIOR_LABEL: Record<string, string> = {
  '7d': 'vs prior 7 days',
  '30d': 'vs prior 30 days',
  '90d': 'vs prior 90 days',
  yoy: 'vs last year',
}

export function priorLabel(timeWindow: string | undefined): string {
  return PRIOR_LABEL[timeWindow ?? '30d'] ?? 'vs prior period'
}

/** A KPI delta line: "+12% vs prior 30 days", with sign + tone. */
export function formatDelta(deltaPct: number | null, timeWindow: string | undefined) {
  if (deltaPct == null) return null
  const pct = Math.round(deltaPct * 100)
  const sign = pct > 0 ? '+' : ''
  const tone = pct > 0 ? 'text-success' : pct < 0 ? 'text-error' : 'text-muted-foreground'
  return { text: `${sign}${pct}% ${priorLabel(timeWindow)}`, tone }
}

/** Format a KpiMetric value by its unit. */
export function formatKpi(value: number | null, unit: string): string {
  if (value == null) return '—'
  if (unit === 'percent') return `${Math.round(value * 100)}%`
  if (unit === 'score') return `${Math.round(value * 100)}`
  return value.toLocaleString()
}

export function titleCase(s: string): string {
  return s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}
