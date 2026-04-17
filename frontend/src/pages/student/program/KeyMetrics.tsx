import { DollarSign, Percent, TrendingUp, GraduationCap, Target } from 'lucide-react'
import { formatCurrency } from '../../../utils/format'

/**
 * KeyMetrics — compact hero strip of the 4–5 most important stats for a
 * program. Each tile gets a tone (colored accent), a context label (e.g.,
 * "highly selective"), and shows a blank state when the value is missing
 * so the strip stays visually balanced.
 *
 * Secondary stats (SAT, ACT, retention, debt, pell, net price, etc.) live
 * in their respective tabs — this strip is the "what matters most" summary.
 */

interface Props {
  acceptanceRate?: number | null
  medianSalary?: number | null
  tuition?: number | null
  graduationRate?: number | null
  employmentRate?: number | null
}

type Tone = 'amber' | 'emerald' | 'rose' | 'blue' | 'slate'

const TONE: Record<Tone, { bg: string; border: string; text: string; icon: string; chip: string }> = {
  amber:   { bg: 'bg-amber-50/70',   border: 'border-amber-200/60',   text: 'text-amber-900',   icon: 'text-amber-600',   chip: 'bg-amber-100 text-amber-700' },
  emerald: { bg: 'bg-emerald-50/70', border: 'border-emerald-200/60', text: 'text-emerald-900', icon: 'text-emerald-600', chip: 'bg-emerald-100 text-emerald-700' },
  rose:    { bg: 'bg-rose-50/70',    border: 'border-rose-200/60',    text: 'text-rose-900',    icon: 'text-rose-600',    chip: 'bg-rose-100 text-rose-700' },
  blue:    { bg: 'bg-blue-50/70',    border: 'border-blue-200/60',    text: 'text-blue-900',    icon: 'text-blue-600',    chip: 'bg-blue-100 text-blue-700' },
  slate:   { bg: 'bg-slate-50',      border: 'border-slate-200',      text: 'text-slate-800',   icon: 'text-slate-500',   chip: 'bg-slate-200 text-slate-700' },
}

interface Tile {
  icon: typeof DollarSign
  label: string
  value: string
  context?: string | null
  tone: Tone
  empty?: boolean
}

function acceptanceContext(rate: number): string {
  const pct = rate * 100
  if (pct < 10) return 'Highly selective'
  if (pct < 25) return 'Very selective'
  if (pct < 50) return 'Selective'
  return 'Accessible'
}

function salaryContext(salary: number): string {
  if (salary >= 100000) return 'Top decile'
  if (salary >= 80000) return 'Top quartile'
  if (salary >= 60000) return 'Above average'
  return 'Typical'
}

function gradRateContext(rate: number): string {
  const pct = rate * 100
  if (pct >= 90) return 'Exceptional'
  if (pct >= 80) return 'Strong'
  if (pct >= 70) return 'Average'
  return 'Below average'
}

function tuitionContext(tuition: number): string {
  if (tuition >= 60000) return 'Premium'
  if (tuition >= 40000) return 'High'
  if (tuition >= 20000) return 'Moderate'
  return 'Affordable'
}

export default function KeyMetrics({
  acceptanceRate,
  medianSalary,
  tuition,
  graduationRate,
  employmentRate,
}: Props) {
  const tiles: Tile[] = []

  tiles.push({
    icon: Percent,
    label: 'Acceptance',
    value: acceptanceRate != null ? `${(acceptanceRate * 100).toFixed(acceptanceRate < 0.1 ? 1 : 0)}%` : '—',
    context: acceptanceRate != null ? acceptanceContext(acceptanceRate) : 'Data not reported',
    tone: 'amber',
    empty: acceptanceRate == null,
  })

  tiles.push({
    icon: TrendingUp,
    label: 'Avg Salary',
    value: medianSalary != null ? formatCurrency(medianSalary) : '—',
    context: medianSalary != null ? salaryContext(medianSalary) : 'Data not reported',
    tone: 'emerald',
    empty: medianSalary == null,
  })

  tiles.push({
    icon: DollarSign,
    label: 'Tuition / yr',
    value: tuition != null ? formatCurrency(tuition) : '—',
    context: tuition != null ? tuitionContext(tuition) : 'Data not reported',
    tone: 'rose',
    empty: tuition == null,
  })

  tiles.push({
    icon: GraduationCap,
    label: 'Grad Rate',
    value: graduationRate != null ? `${Math.round(graduationRate * 100)}%` : '—',
    context: graduationRate != null ? gradRateContext(graduationRate) : 'Data not reported',
    tone: 'blue',
    empty: graduationRate == null,
  })

  if (employmentRate != null) {
    tiles.push({
      icon: Target,
      label: 'Employment',
      value: `${Math.round(employmentRate * 100)}%`,
      context: 'Within 6 months',
      tone: 'emerald',
    })
  }

  return (
    <div className="mb-5">
      <div className={`grid gap-2 ${tiles.length >= 5 ? 'grid-cols-2 md:grid-cols-3 lg:grid-cols-5' : 'grid-cols-2 md:grid-cols-4'}`}>
        {tiles.map((t, i) => {
          const tone = t.empty ? TONE.slate : TONE[t.tone]
          return (
            <div
              key={i}
              className={`relative rounded-xl border px-3.5 py-3 ${tone.bg} ${tone.border} transition-all hover:shadow-sm`}
            >
              <div className="flex items-start justify-between mb-1.5">
                <div className={`w-7 h-7 rounded-lg bg-white flex items-center justify-center ${tone.icon}`}>
                  <t.icon size={13} />
                </div>
                {t.context && !t.empty && (
                  <span className={`text-[9px] font-semibold uppercase tracking-wide px-1.5 py-0.5 rounded-md ${tone.chip}`}>
                    {t.context}
                  </span>
                )}
              </div>
              <p className={`text-[10px] uppercase tracking-wider font-semibold ${t.empty ? 'text-slate-400' : 'text-student-text/70'}`}>
                {t.label}
              </p>
              <p className={`text-[22px] font-bold leading-tight mt-0.5 ${t.empty ? 'text-slate-300' : tone.text}`}>
                {t.value}
              </p>
              {t.empty && t.context && (
                <p className="text-[10px] text-slate-400 italic mt-0.5">{t.context}</p>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
