import {
  DollarSign, TrendingUp, GraduationCap, Target, Clock, Wallet,
  Briefcase, Award, Users, Sparkles, ArrowUpRight,
} from 'lucide-react'
import { formatCurrency } from '../../../utils/format'

/**
 * KeyMetrics — 4 tiles showing what makes THIS program characteristic.
 *
 * Principle: tiles should highlight what's attractive about the program —
 * outcomes, ROI, structure, opportunities. NOT friction/difficulty metrics
 * like acceptance rate or app requirements count — those belong in the
 * Admissions tab. Every program is different, so we compute every possible
 * positive/characteristic metric and pick the top 4.
 *
 * Priorities (all positive / characteristic, no friction metrics):
 *   1. Program-specific outcomes (employment rate, median salary, hiring partners)
 *   2. ROI signals (payback period, salary growth trajectory)
 *   3. Program character (duration, specializations, highlights count, total investment)
 *   4. Institution outcome rollups (mid-career earnings, grad rate) as fallback
 */

type Tone = 'amber' | 'emerald' | 'rose' | 'blue' | 'violet' | 'slate'

const TONE: Record<Tone, { bg: string; border: string; text: string; icon: string; chip: string }> = {
  amber:   { bg: 'bg-amber-50/70',   border: 'border-amber-200/60',   text: 'text-amber-900',   icon: 'text-amber-600',   chip: 'bg-amber-100 text-amber-700' },
  emerald: { bg: 'bg-emerald-50/70', border: 'border-emerald-200/60', text: 'text-emerald-900', icon: 'text-emerald-600', chip: 'bg-emerald-100 text-emerald-700' },
  rose:    { bg: 'bg-rose-50/70',    border: 'border-rose-200/60',    text: 'text-rose-900',    icon: 'text-rose-600',    chip: 'bg-rose-100 text-rose-700' },
  blue:    { bg: 'bg-blue-50/70',    border: 'border-blue-200/60',    text: 'text-blue-900',    icon: 'text-blue-600',    chip: 'bg-blue-100 text-blue-700' },
  violet:  { bg: 'bg-violet-50/70',  border: 'border-violet-200/60',  text: 'text-violet-900',  icon: 'text-violet-600',  chip: 'bg-violet-100 text-violet-700' },
  slate:   { bg: 'bg-slate-50',      border: 'border-slate-200',      text: 'text-slate-800',   icon: 'text-slate-500',   chip: 'bg-slate-200 text-slate-700' },
}

interface Tile {
  icon: typeof DollarSign
  label: string
  value: string
  context?: string
  tone: Tone
}

interface Props {
  // Program shape
  degreeType?: string | null
  durationMonths?: number | null
  tuition?: number | null
  tracks?: string[] | null
  applicationRequirements?: any[] | null
  highlights?: string[] | null

  // Program-specific outcomes (from outcomes_data)
  outcomesMedianSalary?: number | null
  outcomesEmploymentRate?: number | null
  outcomesInternshipConversion?: number | null
  outcomesTopEmployers?: string[] | null
  outcomesPaybackMonths?: number | null

  // Institution rollups (fallback)
  institutionTuition?: number | null
  earnings6yr?: number | null
  earnings10yr?: number | null
  graduationRate?: number | null
  retentionRate?: number | null
}

const DEFAULT_DURATION_MONTHS: Record<string, number> = {
  bachelors: 48,
  masters: 24,
  phd: 60,
  certificate: 12,
  doctorate: 60,
  associate: 24,
}

function formatDurationYears(months: number): { value: string; context: string } {
  if (months < 12) return { value: `${months} mo`, context: months === 1 ? 'Short program' : 'Accelerated' }
  const years = months / 12
  const display = Number.isInteger(years) ? `${years}` : years.toFixed(1)
  const ctx = months <= 12 ? 'Accelerated' : months <= 24 ? 'Graduate track' : months <= 36 ? 'Standard' : 'Full undergrad'
  return { value: `${display} years`, context: ctx }
}

function salaryGrowthContext(pct: number): string {
  if (pct >= 40) return 'Exceptional growth'
  if (pct >= 25) return 'Strong growth'
  if (pct >= 10) return 'Steady growth'
  return 'Modest growth'
}

export default function KeyMetrics(props: Props) {
  const candidates: Tile[] = []

  // Derive duration from degree type if not explicitly set, so every program
  // has a duration tile to show.
  const effectiveDuration = props.durationMonths ?? (props.degreeType ? DEFAULT_DURATION_MONTHS[props.degreeType] : null)
  // Fall back to institution tuition when program-level tuition isn't set.
  const effectiveTuition = props.tuition ?? props.institutionTuition ?? null

  // ── Tier 1: Program-specific outcomes (if present) ──
  if (props.outcomesMedianSalary) {
    candidates.push({
      icon: TrendingUp,
      label: 'Median Salary',
      value: formatCurrency(props.outcomesMedianSalary),
      context: 'Reported by program',
      tone: 'emerald',
    })
  }
  if (props.outcomesEmploymentRate != null) {
    candidates.push({
      icon: Briefcase,
      label: 'Employment Rate',
      value: `${Math.round(props.outcomesEmploymentRate * 100)}%`,
      context: 'Within 6 months',
      tone: 'emerald',
    })
  }
  if (props.outcomesInternshipConversion != null) {
    candidates.push({
      icon: ArrowUpRight,
      label: 'Intern → Offer',
      value: `${Math.round(props.outcomesInternshipConversion * 100)}%`,
      context: 'Conversion rate',
      tone: 'violet',
    })
  }
  if (props.outcomesTopEmployers && props.outcomesTopEmployers.length > 0) {
    candidates.push({
      icon: Award,
      label: 'Hiring Partners',
      value: `${props.outcomesTopEmployers.length}${props.outcomesTopEmployers.length >= 5 ? '+' : ''}`,
      context: props.outcomesTopEmployers.slice(0, 2).join(', '),
      tone: 'violet',
    })
  }
  if (props.outcomesPaybackMonths) {
    const yrs = (props.outcomesPaybackMonths / 12).toFixed(1)
    candidates.push({
      icon: Wallet,
      label: 'Payback Period',
      value: `${yrs} yrs`,
      context: 'To recoup tuition',
      tone: 'blue',
    })
  }

  // ── Tier 2: Calculated program metrics ──
  if (effectiveTuition && effectiveDuration) {
    const years = effectiveDuration / 12
    const total = effectiveTuition * years
    candidates.push({
      icon: DollarSign,
      label: 'Total Investment',
      value: formatCurrency(total),
      context: `${years % 1 === 0 ? years : years.toFixed(1)} yrs × ${formatCurrency(effectiveTuition)}`,
      tone: 'rose',
    })
  } else if (effectiveTuition) {
    candidates.push({
      icon: DollarSign,
      label: 'Tuition / yr',
      value: formatCurrency(effectiveTuition),
      context: 'Per academic year',
      tone: 'rose',
    })
  }

  if (props.earnings6yr && props.earnings10yr && props.earnings10yr > props.earnings6yr) {
    const growth = ((props.earnings10yr - props.earnings6yr) / props.earnings6yr) * 100
    candidates.push({
      icon: TrendingUp,
      label: 'Salary Growth',
      value: `+${growth.toFixed(0)}%`,
      context: salaryGrowthContext(growth),
      tone: 'emerald',
    })
  }

  // ── Tier 3: Program shape ──
  if (effectiveDuration) {
    const d = formatDurationYears(effectiveDuration)
    candidates.push({
      icon: Clock,
      label: 'Duration',
      value: d.value,
      context: d.context,
      tone: 'blue',
    })
  }

  if (props.tracks && props.tracks.length > 0) {
    candidates.push({
      icon: Sparkles,
      label: 'Specializations',
      value: String(props.tracks.length),
      context: props.tracks.slice(0, 2).join(', '),
      tone: 'violet',
    })
  }

  // application_requirements count intentionally NOT shown here — it reads as a
  // barrier ("how hard is it to apply?") and belongs in the Admissions tab.

  if (props.highlights && props.highlights.length > 0) {
    candidates.push({
      icon: Sparkles,
      label: 'Program Highlights',
      value: `${props.highlights.length}`,
      context: 'Distinctive features',
      tone: 'violet',
    })
  }

  // ── Tier 4: Institution rollups (fallback) ──
  if (props.earnings10yr && !props.outcomesMedianSalary) {
    candidates.push({
      icon: TrendingUp,
      label: 'Mid-Career (10yr)',
      value: formatCurrency(props.earnings10yr),
      context: 'Median graduate earnings',
      tone: 'emerald',
    })
  }
  if (props.earnings6yr && !candidates.some(c => c.label.startsWith('Mid-Career'))) {
    candidates.push({
      icon: TrendingUp,
      label: 'Early Career (6yr)',
      value: formatCurrency(props.earnings6yr),
      context: '6 years after enrollment',
      tone: 'emerald',
    })
  }

  if (props.graduationRate != null) {
    candidates.push({
      icon: GraduationCap,
      label: 'Grad Rate',
      value: `${Math.round(props.graduationRate * 100)}%`,
      context: props.graduationRate > 0.85 ? 'Well above average' : props.graduationRate > 0.7 ? 'Above average' : 'Typical',
      tone: 'blue',
    })
  }

  if (props.retentionRate != null && candidates.length < 8) {
    candidates.push({
      icon: Target,
      label: 'Retention',
      value: `${Math.round(props.retentionRate * 100)}%`,
      context: 'First-year return',
      tone: 'blue',
    })
  }

  // ── Pick top 4, deduping salary-family tiles so we don't show 3 salary numbers ──
  const picked: Tile[] = []
  let salaryCount = 0
  for (const c of candidates) {
    if (picked.length >= 4) break
    const isSalary = /salary|earnings|growth|career/i.test(c.label)
    if (isSalary && salaryCount >= 2) continue
    if (isSalary) salaryCount++
    picked.push(c)
  }

  // If we still don't have 4, pad with slate placeholders so the grid stays balanced
  while (picked.length < 4) {
    picked.push({
      icon: Users,
      label: 'Data coming soon',
      value: '—',
      context: 'Not reported yet',
      tone: 'slate',
    })
  }

  return (
    <div className="mb-5">
      <div className="grid gap-2 grid-cols-2 md:grid-cols-4">
        {picked.map((t, i) => {
          const tone = TONE[t.tone]
          const isEmpty = t.value === '—'
          return (
            <div
              key={i}
              className={`relative rounded-xl border px-3.5 py-3 ${tone.bg} ${tone.border} transition-all hover:shadow-sm`}
            >
              <div className="flex items-start justify-between mb-1.5">
                <div className={`w-7 h-7 rounded-lg bg-white flex items-center justify-center ${tone.icon}`}>
                  <t.icon size={13} />
                </div>
                {t.context && !isEmpty && (
                  <span className={`text-[9px] font-semibold uppercase tracking-wide px-1.5 py-0.5 rounded-md ${tone.chip} max-w-[130px] truncate`}>
                    {t.context}
                  </span>
                )}
              </div>
              <p className={`text-[10px] uppercase tracking-wider font-semibold ${isEmpty ? 'text-slate-400' : 'text-student-text/70'}`}>
                {t.label}
              </p>
              <p className={`text-[22px] font-bold leading-tight mt-0.5 ${isEmpty ? 'text-slate-300' : tone.text}`}>
                {t.value}
              </p>
              {isEmpty && t.context && (
                <p className="text-[10px] text-slate-400 italic mt-0.5">{t.context}</p>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
