import {
  DollarSign, TrendingUp, GraduationCap, Clock,
  Briefcase, Award, Sparkles, BookOpen, MapPin,
  Microscope, Users, Compass,
} from 'lucide-react'
import { formatCurrency } from '../../../utils/format'

/**
 * KeyMetrics — 4 tiles that show what's *distinctive* about THIS program.
 *
 * Rules:
 * - Every tile should answer "what's unusual or advantageous here?"
 * - Prefer concrete numbers over abstract ratings ("$64K → $82K" > "+28% growth")
 * - Parse highlights/description text to surface program-specific facts
 *   (credits, honors, subfields, location advantages)
 * - Hide tiles that are the same for most programs (standard duration, standard
 *   credits) — they're noise, not signal
 * - Friction metrics (acceptance rate, requirement count) never go here; they
 *   belong in the Admissions tab
 */

type Tone = 'amber' | 'emerald' | 'rose' | 'blue' | 'violet' | 'slate'

interface Tile {
  icon: typeof DollarSign
  label: string
  value: string
  context?: string
  tone: Tone
  priority: number // higher = more distinctive, picked first
  /** Source attribution (rendered as an (i) tooltip next to the subtitle). */
  sourceNote?: string
}

interface Props {
  // Program shape
  degreeType?: string | null
  durationMonths?: number | null
  tuition?: number | null
  tracks?: string[] | null
  applicationRequirements?: any[] | null
  highlights?: string[] | null
  descriptionText?: string | null

  // Program-specific outcomes (from outcomes_data) — Section A of the strip.
  // All Section A tiles are anchored to canonical timeframes:
  //   Salary = 4 years after graduation (College Scorecard program-level)
  //   Employment = 6 months after graduation
  //   Employers / Industries = past 3 years of graduates
  /** College Scorecard canonical earnings at 4 years after graduation. */
  outcomesEarnings4yr?: number | null
  /** Freeform program-reported median salary (only used if salary_timeframe matches canonical). */
  outcomesMedianSalary?: number | null
  outcomesEmploymentRate?: number | null
  outcomesTopEmployers?: string[] | null
  outcomesTopIndustries?: string[] | null
  /** When the median-salary snapshot was taken, e.g. "4 years after graduation". */
  outcomesSalaryTimeframe?: string | null
  /** When employment was measured, e.g. "6 months after graduation". */
  outcomesEmploymentTimeframe?: string | null
  /** Source of the outcomes data, e.g. "College Scorecard" or "School career services". */
  outcomesSource?: string | null

  // Cost breakdown (from cost_data)
  costFees?: Record<string, number> | null
  costLiving?: number | null
  costBooks?: number | null
  totalCostAttendance?: number | null

  // Institution rollups (fallback)
  institutionTuition?: number | null
  graduationRate?: number | null
  retentionRate?: number | null
}

/** Section A tile labels — used by the picker to enforce "max 1 Section A tile". */
const SECTION_A_LABELS = new Set([
  'Median Salary',
  'Employment Rate',
  'Top Employers',
  'Top Industries',
])

/* ── Constants ─────────────────────────────────────────────────────────── */

const DEFAULT_DURATION_MONTHS: Record<string, number> = {
  bachelors: 48, masters: 24, phd: 60, certificate: 12, doctorate: 60, associate: 24,
}

const DEFAULT_CREDITS: Record<string, number> = {
  bachelors: 120, masters: 30, phd: 60, certificate: 12, associate: 60,
}

/* ── Parsers: extract distinctive facts from unstructured text ─────────── */

const WORD_NUMBERS: Record<string, number> = {
  two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8, nine: 9, ten: 10, eleven: 11, twelve: 12,
}

function parseNumberWord(s: string): number | null {
  const n = parseInt(s, 10)
  if (!isNaN(n)) return n
  return WORD_NUMBERS[s.toLowerCase()] ?? null
}

/**
 * Parse program highlights for specific facts we can surface as tiles:
 *   - credit count ("128-credit curriculum")
 *   - honors option ("Honors track for 3.65+ GPA")
 *   - location ("Located in Greenwich Village")
 *   - specific counts ("4 research labs", "6 concentrations")
 */
function tilesFromHighlights(highlights: string[], degreeType: string): Tile[] {
  const tiles: Tile[] = []
  const seen = new Set<string>() // dedupe by tile label

  for (const raw of highlights) {
    const h = raw.trim()
    if (!h) continue

    // Credits: "128-credit" / "128 credit" / "128 credits"
    const creditMatch = h.match(/(\d{2,3})[-\s]credits?/i)
    if (creditMatch && !seen.has('credits')) {
      const n = parseInt(creditMatch[1], 10)
      const std = DEFAULT_CREDITS[degreeType]
      // Only show if meaningfully different from standard
      const isDistinctive = !std || Math.abs(n - std) >= 4
      if (isDistinctive) {
        tiles.push({
          icon: BookOpen,
          label: 'Credits',
          value: `${n}`,
          context: n > (std ?? 120) ? 'Comprehensive' : n < (std ?? 120) ? 'Compact' : 'Standard',
          tone: 'violet',
          priority: 55,
        })
        seen.add('credits')
      }
    }

    // Honors / thesis / research track
    if (/honors|thesis|research\s+track/i.test(h) && !seen.has('honors')) {
      const gpaMatch = h.match(/(\d\.\d+)\+?\s*GPA/i)
      tiles.push({
        icon: Award,
        label: /thesis/i.test(h) ? 'Thesis Track' : 'Honors Track',
        value: 'Available',
        context: gpaMatch ? `${gpaMatch[1]}+ GPA path` : 'Advanced pathway',
        tone: 'amber',
        priority: 62,
      })
      seen.add('honors')
    }

    // Campus location: "Located in Greenwich Village" / "Campus in Palo Alto"
    const locationMatch = h.match(/(?:located|campus|based)\s+in\s+([A-Z][A-Za-z\s]{3,30}?)(?:\.|,|$|—)/i)
    if (locationMatch && !seen.has('location')) {
      const loc = locationMatch[1].trim()
      tiles.push({
        icon: MapPin,
        label: 'Campus',
        value: loc,
        context: 'Location advantage',
        tone: 'blue',
        priority: 52,
      })
      seen.add('location')
    }

    // Research / labs / partnerships
    const labsMatch = h.match(/(\d+)\+?\s*(research\s+)?(labs?|laboratories|research\s+centers?)/i)
    if (labsMatch && !seen.has('labs')) {
      tiles.push({
        icon: Microscope,
        label: 'Research Labs',
        value: `${labsMatch[1]}+`,
        context: 'Hands-on opportunities',
        tone: 'violet',
        priority: 60,
      })
      seen.add('labs')
    }

    // Study abroad / international
    if (/study\s+abroad|international\s+exchange/i.test(h) && !seen.has('abroad')) {
      tiles.push({
        icon: Compass,
        label: 'Study Abroad',
        value: 'Available',
        context: 'Global programs',
        tone: 'violet',
        priority: 50,
      })
      seen.add('abroad')
    }
  }

  return tiles
}

/** Parse description text for subfield / concentration counts.
 *  e.g., "four principal subfields: cultural anthropology, archaeology..." */
function subfieldsFromDescription(desc?: string | null): Tile | null {
  if (!desc) return null
  const m = desc.match(/\b(\d+|two|three|four|five|six|seven|eight|nine|ten)\s+(principal\s+|main\s+|core\s+|primary\s+|major\s+)?(subfields?|concentrations?|tracks?|specializations?|streams?|pathways?|areas?\s+of\s+(?:study|focus))/i)
  if (!m) return null
  const n = parseNumberWord(m[1])
  if (!n) return null
  const kind = m[3].replace(/s$/, '').replace(/\s+of\s+(study|focus)/, '').trim()
  return {
    icon: Sparkles,
    label: `${kind.charAt(0).toUpperCase()}${kind.slice(1)}s`,
    value: String(n),
    context: 'Areas of focus',
    tone: 'violet',
    priority: 68,
  }
}

/* ── Utility formatters ────────────────────────────────────────────────── */

function shortCurrency(n: number): string {
  if (n >= 1000) return `$${Math.round(n / 1000)}K`
  return `$${n}`
}

function formatDurationYears(months: number): string {
  if (months < 12) return `${months} mo`
  const years = months / 12
  return Number.isInteger(years) ? `${years} yr${years > 1 ? 's' : ''}` : `${years.toFixed(1)} yrs`
}

/* ── Main component ────────────────────────────────────────────────────── */

export default function KeyMetrics(props: Props) {
  const candidates: Tile[] = []
  const degreeType = props.degreeType ?? 'bachelors'

  const effectiveDuration = props.durationMonths ?? DEFAULT_DURATION_MONTHS[degreeType] ?? null
  const effectiveTuition = props.tuition ?? props.institutionTuition ?? null

  /* ── Section A: Program-Reported Outcomes ────────────────────────────────
   *
   * Every Section A tile is anchored to a canonical timeframe so cross-program
   * comparison is meaningful:
   *   Salary     → 4 years after graduation (College Scorecard)
   *   Employment → 6 months after graduation
   *   Employers  → past 3 years of graduates
   *   Industries → past 3 years of graduates
   *
   * All tiles render emerald. Source attribution appears as a small (i) icon
   * next to the subtitle. The picker enforces "max 1 Section A tile" further
   * down, so within this group only the highest-priority qualifier makes the
   * final strip (priority order: Salary > Employment > Employers > Industries).
   */

  // Source note shared by every Section A tile when outcomes_data.source is set.
  const sectionASource = props.outcomesSource || undefined

  // 1. Median Salary — prefer the Scorecard canonical field; accept a freeform
  //    median_salary only when the reported timeframe explicitly matches 4 yrs.
  const canonicalSalary = props.outcomesEarnings4yr
    ?? (props.outcomesMedianSalary != null
        && /4\s?yr|4\s?years/i.test(props.outcomesSalaryTimeframe || '')
        ? props.outcomesMedianSalary
        : null)
  if (canonicalSalary) {
    candidates.push({
      icon: TrendingUp,
      label: 'Median Salary',
      value: formatCurrency(canonicalSalary),
      context: '4 yrs after graduation',
      tone: 'emerald',
      priority: 95,
      sourceNote: sectionASource,
    })
  }

  // 2. Employment Rate — must be at the canonical 6-month timeframe. We accept
  //    null/unset timeframe as the canonical default (backwards-compatible).
  const employmentTimeframeOk = !props.outcomesEmploymentTimeframe
    || /6\s?mo|6\s?months/i.test(props.outcomesEmploymentTimeframe)
  if (props.outcomesEmploymentRate != null && employmentTimeframeOk) {
    candidates.push({
      icon: Briefcase,
      label: 'Employment Rate',
      value: `${Math.round(props.outcomesEmploymentRate * 100)}%`,
      context: '6 mo after graduation',
      tone: 'emerald',
      priority: 94,
      sourceNote: sectionASource,
    })
  }

  // 3. Top Employers — show up to 3, emerald tone, canonical "past 3 years".
  if (props.outcomesTopEmployers && props.outcomesTopEmployers.length > 0) {
    candidates.push({
      icon: Award,
      label: 'Top Employers',
      value: props.outcomesTopEmployers.slice(0, 3).join(', '),
      context: 'Past 3 years of grads',
      tone: 'emerald',
      priority: 93,
      sourceNote: sectionASource,
    })
  }

  // 4. Top Industries — same treatment.
  if (props.outcomesTopIndustries && props.outcomesTopIndustries.length > 0) {
    candidates.push({
      icon: Users,
      label: 'Top Industries',
      value: props.outcomesTopIndustries.slice(0, 3).join(', '),
      context: 'Past 3 years of grads',
      tone: 'emerald',
      priority: 92,
      sourceNote: sectionASource,
    })
  }

  /* ── Tier 2: Program economics — show what the cost consists of ── */

  // Build an honest breakdown label so students know exactly what's included.
  const costBreakdown: string[] = ['Tuition']
  const fees = props.costFees ? Object.values(props.costFees).reduce((s, v) => s + (Number(v) || 0), 0) : 0
  if (fees > 0) costBreakdown.push('fees')
  if (props.costLiving) costBreakdown.push('housing')
  if (props.costBooks) costBreakdown.push('books')
  const hasComprehensive = fees > 0 || props.costLiving || props.costBooks
  const annualComprehensive = (effectiveTuition || 0) + fees + (props.costLiving || 0) + (props.costBooks || 0)

  if (effectiveTuition && effectiveDuration) {
    const years = effectiveDuration / 12
    const yearsDisplay = years % 1 === 0 ? years : years.toFixed(1)

    if (hasComprehensive) {
      // Full cost of attendance when we can compute it
      const total = annualComprehensive * years
      candidates.push({
        icon: DollarSign,
        label: 'Total Investment',
        value: formatCurrency(total),
        context: `${costBreakdown.join(' + ')} · ${yearsDisplay} yrs × ${shortCurrency(annualComprehensive)}/yr`,
        tone: 'rose',
        priority: 66,
      })
    } else {
      // Tuition-only fallback — be explicit about what's excluded
      const total = effectiveTuition * years
      candidates.push({
        icon: DollarSign,
        label: 'Total Investment',
        value: formatCurrency(total),
        context: `Tuition only · ${yearsDisplay} yrs × ${shortCurrency(effectiveTuition)}/yr (excl. housing)`,
        tone: 'rose',
        priority: 66,
      })
    }
  } else if (effectiveTuition) {
    if (hasComprehensive) {
      candidates.push({
        icon: DollarSign,
        label: 'Cost / yr',
        value: formatCurrency(annualComprehensive),
        context: costBreakdown.join(' + '),
        tone: 'rose',
        priority: 54,
      })
    } else {
      candidates.push({
        icon: DollarSign,
        label: 'Tuition / yr',
        value: formatCurrency(effectiveTuition),
        context: 'Tuition only · excl. housing & living',
        tone: 'rose',
        priority: 50,
      })
    }
  }

  /* ── Tier 4: Program character — parsed from highlights + description ── */

  if (props.highlights) {
    candidates.push(...tilesFromHighlights(props.highlights, degreeType))
  }

  const subfieldsTile = subfieldsFromDescription(props.descriptionText)
  if (subfieldsTile) candidates.push(subfieldsTile)

  // Specializations from structured tracks field. Tracks can be either an
  // array of names or a dict like { concentrations: [...], note: '...' } — the
  // DB shape varies per program, so we normalize before using it.
  const trackNames: string[] = (() => {
    const t: any = props.tracks
    if (!t) return []
    if (Array.isArray(t)) return t.filter((x: any) => typeof x === 'string')
    if (typeof t === 'object') {
      for (const key of ['concentrations', 'tracks', 'subfields', 'specializations', 'streams', 'pathways']) {
        if (Array.isArray(t[key])) return t[key].filter((x: any) => typeof x === 'string')
      }
    }
    return []
  })()

  if (trackNames.length > 0) {
    candidates.push({
      icon: Sparkles,
      label: 'Specializations',
      value: String(trackNames.length),
      context: trackNames.slice(0, 2).join(', '),
      tone: 'violet',
      priority: 64,
    })
  }

  /* ── Tier 5: Duration — only when it's actually distinctive ── */

  if (effectiveDuration) {
    const std = DEFAULT_DURATION_MONTHS[degreeType]
    // Only show duration if it's meaningfully different from the norm for this degree type.
    // A 4-year Bachelor's isn't interesting; a 3-year accelerated one is.
    const isDistinctive = !std || Math.abs(effectiveDuration - std) >= 6
    if (isDistinctive) {
      const fast = std && effectiveDuration < std
      candidates.push({
        icon: Clock,
        label: 'Duration',
        value: formatDurationYears(effectiveDuration),
        context: fast ? 'Accelerated track' : effectiveDuration <= 24 ? 'Graduate track' : 'Extended program',
        tone: 'blue',
        priority: 58,
      })
    }
  }

  /* ── Tier 6: Institution rollups (last-resort fallback) ── */

  if (props.graduationRate != null) {
    candidates.push({
      icon: GraduationCap,
      label: 'Grad Rate',
      value: `${Math.round(props.graduationRate * 100)}%`,
      context: props.graduationRate > 0.85 ? 'Well above avg' : props.graduationRate > 0.7 ? 'Above avg' : 'Typical',
      tone: 'blue',
      priority: 40,
    })
  }

  if (props.retentionRate != null) {
    candidates.push({
      icon: Users,
      label: 'Retention',
      value: `${Math.round(props.retentionRate * 100)}%`,
      context: 'First-year return',
      tone: 'blue',
      priority: 38,
    })
  }

  /* ── Pick top 4 by priority, with soft de-duping ── */

  // Sort by priority, highest first
  candidates.sort((a, b) => b.priority - a.priority)

  const picked: Tile[] = []
  let violetTiles = 0
  let sectionATiles = 0 // enforce "one Section A tile per strip"

  for (const c of candidates) {
    if (picked.length >= 4) break
    const isSectionA = SECTION_A_LABELS.has(c.label)
    if (isSectionA && sectionATiles >= 1) continue // one Section A slot only
    if (c.tone === 'violet' && violetTiles >= 2) continue // avoid over-purpling
    if (isSectionA) sectionATiles++
    if (c.tone === 'violet') violetTiles++
    picked.push(c)
  }

  // If we genuinely can't find 4 real tiles, show what we have — don't pad.
  if (picked.length === 0) return null

  return (
    <div className="mb-5">
      <div className={`grid gap-3 grid-cols-2 ${picked.length >= 4 ? 'md:grid-cols-4' : picked.length === 3 ? 'md:grid-cols-3' : 'md:grid-cols-2'}`}>
        {picked.map((t, i) => <MetricTile key={i} tile={t} />)}
      </div>
    </div>
  )
}

/* ── Tile render — editorial-style card with left accent + mini viz ──── */

/** Helpers that map tone → specific utility classes. We keep these close to
 *  the render function because they only matter for presentation. */
const ACCENT_BG: Record<Tone, string> = {
  amber: 'bg-amber-500',
  emerald: 'bg-emerald-500',
  rose: 'bg-rose-500',
  blue: 'bg-blue-500',
  violet: 'bg-violet-500',
  slate: 'bg-slate-400',
}
const ICON_COLOR: Record<Tone, string> = {
  amber: 'text-amber-600',
  emerald: 'text-emerald-600',
  rose: 'text-rose-600',
  blue: 'text-blue-600',
  violet: 'text-violet-600',
  slate: 'text-slate-500',
}
const VALUE_COLOR: Record<Tone, string> = {
  amber: 'text-amber-900',
  emerald: 'text-emerald-900',
  rose: 'text-rose-900',
  blue: 'text-blue-900',
  violet: 'text-violet-900',
  slate: 'text-slate-800',
}

function MetricTile({ tile }: { tile: Tile }) {
  const Icon = tile.icon

  return (
    <div className="group relative rounded-xl bg-white border border-divider pl-4 pr-4 py-4 transition-all hover:-translate-y-0.5 hover:shadow-lg hover:border-slate-300 overflow-hidden">
      {/* Left accent bar — the only bg color on the tile */}
      <span className={`absolute left-0 top-0 bottom-0 w-[3px] ${ACCENT_BG[tile.tone]}`} aria-hidden />

      {/* Eyebrow: icon + label */}
      <div className="flex items-center gap-2 mb-2.5">
        <Icon size={12} className={ICON_COLOR[tile.tone]} />
        <span className="text-[10px] uppercase tracking-[0.08em] font-semibold text-slate-500">
          {tile.label}
        </span>
      </div>

      {/* Hero value — bold, tabular, truncates if too wide */}
      <p
        className={`text-[26px] font-bold tracking-tight tabular-nums leading-[1.1] ${VALUE_COLOR[tile.tone]} truncate`}
        title={tile.value}
      >
        {tile.value}
      </p>

      {/* Context — editorial subtitle, optionally followed by an (i) source tooltip */}
      {(tile.context || tile.sourceNote) && (
        <p className="text-[11.5px] text-slate-500 mt-2 leading-snug line-clamp-2">
          {tile.context}
          {tile.sourceNote && (
            <span
              className="inline-flex items-center justify-center w-3.5 h-3.5 rounded-full bg-slate-100 text-slate-500 text-[9px] font-semibold ml-1 cursor-help select-none hover:bg-slate-200 hover:text-slate-700 transition-colors align-[1px]"
              title={`Source: ${tile.sourceNote}`}
              aria-label={`Source: ${tile.sourceNote}`}
            >
              i
            </span>
          )}
        </p>
      )}
    </div>
  )
}
