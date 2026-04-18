import { formatCurrency } from '../../../../utils/format'
import { DEGREE_LABELS } from '../../../../utils/constants'
import type { ProgramSummary, MatchResult } from '../../../../types'
import {
  Bookmark, BookmarkCheck, DollarSign, GraduationCap,
  TrendingUp, Percent, ArrowRightLeft,
  Clock, Building, Calendar, ArrowRight, Sparkles,
} from 'lucide-react'
import { differenceInDays } from 'date-fns'

function fitStyle(tier: number) {
  if (tier >= 3) return { text: 'Strong Fit', ring: 'stroke-emerald-500', pill: 'bg-emerald-50 text-emerald-700 border-emerald-200' }
  if (tier >= 2) return { text: 'Good Fit', ring: 'stroke-blue-500', pill: 'bg-blue-50 text-blue-700 border-blue-200' }
  return { text: 'Reach', ring: 'stroke-amber-500', pill: 'bg-amber-50 text-amber-700 border-amber-200' }
}

/**
 * Visual identity per degree — each gets distinct color + icon treatment so
 * cards feel like a family but every card has personality even without an image.
 */
const DEGREE_THEME: Record<string, {
  gradient: string
  accent: string
  chipBg: string
  chipText: string
  ring: string
}> = {
  bachelors: {
    gradient: 'from-blue-500 via-indigo-500 to-indigo-600',
    accent: 'border-l-indigo-500',
    chipBg: 'bg-indigo-50',
    chipText: 'text-indigo-700',
    ring: 'ring-indigo-200',
  },
  masters: {
    gradient: 'from-violet-500 via-purple-500 to-fuchsia-500',
    accent: 'border-l-purple-500',
    chipBg: 'bg-purple-50',
    chipText: 'text-purple-700',
    ring: 'ring-purple-200',
  },
  phd: {
    gradient: 'from-slate-700 via-slate-800 to-zinc-900',
    accent: 'border-l-slate-700',
    chipBg: 'bg-slate-100',
    chipText: 'text-slate-800',
    ring: 'ring-slate-300',
  },
  certificate: {
    gradient: 'from-emerald-500 via-teal-500 to-cyan-500',
    accent: 'border-l-emerald-500',
    chipBg: 'bg-emerald-50',
    chipText: 'text-emerald-700',
    ring: 'ring-emerald-200',
  },
  doctorate: {
    gradient: 'from-rose-500 via-pink-500 to-rose-600',
    accent: 'border-l-rose-500',
    chipBg: 'bg-rose-50',
    chipText: 'text-rose-700',
    ring: 'ring-rose-200',
  },
}

const DEFAULT_THEME = DEGREE_THEME.bachelors

function degreeAbbrev(degree: string): string {
  const map: Record<string, string> = {
    bachelors: 'BS', masters: 'MS', phd: 'PhD',
    certificate: 'CERT', doctorate: 'DOC', associate: 'AA',
  }
  return map[degree] || degree.slice(0, 3).toUpperCase()
}

function formatDuration(months?: number | null): string | null {
  if (!months) return null
  if (months < 12) return `${months} mo`
  const years = months / 12
  return Number.isInteger(years) ? `${years} yr${years > 1 ? 's' : ''}` : `${years.toFixed(1)} yrs`
}

function formatFormat(f?: string | null): string | null {
  if (!f) return null
  const map: Record<string, string> = {
    on_campus: 'On Campus', online: 'Online',
    hybrid: 'Hybrid', in_person: 'In-Person',
  }
  return map[f] || f.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function deadlineInfo(deadline?: string | null) {
  if (!deadline) return null
  const days = differenceInDays(new Date(deadline), new Date())
  const date = new Date(deadline).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  if (days < 0) return { text: date, urgent: false, closed: true }
  if (days <= 30) return { text: `${days}d left`, urgent: true, closed: false, date }
  return { text: date, urgent: false, closed: false }
}

interface Props {
  program: ProgramSummary
  saved: boolean
  match?: MatchResult
  comparing?: boolean
  onSave: () => void
  onCompare?: () => void
  onAskCounselor?: () => void
  onView: () => void
}

export default function ProgramCard({ program, saved, match, comparing, onSave, onCompare, onAskCounselor, onView }: Props) {
  const degree = DEGREE_LABELS[program.degree_type] || program.degree_type
  const abbrev = degreeAbbrev(program.degree_type)
  const theme = DEGREE_THEME[program.degree_type] || DEFAULT_THEME
  const fit = match ? fitStyle(match.match_tier) : null
  const matchScore = match?.match_score != null ? Math.round(match.match_score * 100) : null

  const duration = formatDuration(program.duration_months)
  const format = formatFormat(program.delivery_format)
  const deadline = deadlineInfo(program.application_deadline)

  const acceptPct = program.acceptance_rate != null ? Math.round(program.acceptance_rate * 100) : null
  const gradPct = program.employment_rate != null ? Math.round(program.employment_rate * 100) : null

  // Count meta pills to decide spacing
  const metaItems = [duration, format, deadline ? (deadline.urgent ? `⚡ ${deadline.text}` : deadline.text) : null].filter(Boolean)

  return (
    <div className={`bg-white rounded-2xl border border-divider hover:shadow-xl hover:-translate-y-1 transition-all duration-300 ease-out overflow-hidden flex flex-col group/card border-l-4 ${theme.accent}`}>
      {/* ── Header ── */}
      <div
        onClick={onView}
        className={`relative overflow-hidden cursor-pointer bg-gradient-to-br ${theme.gradient} px-4 pt-4 pb-4`}
      >
        {/* Decorative pattern */}
        <div className="absolute inset-0 opacity-10 pointer-events-none">
          <div className="absolute -right-8 -top-8 w-32 h-32 rounded-full bg-white blur-2xl" />
          <div className="absolute -left-4 -bottom-10 w-24 h-24 rounded-full bg-white/50 blur-xl" />
        </div>

        {/* Save button (floating) */}
        <button
          onClick={e => { e.stopPropagation(); onSave() }}
          className={`absolute top-3 right-3 p-2 rounded-full backdrop-blur-sm transition-all ${
            saved
              ? 'bg-white text-amber-600 shadow-lg'
              : 'bg-white/20 text-white hover:bg-white/40'
          }`}
          aria-label={saved ? 'Unsave program' : 'Save program'}
        >
          {saved ? <BookmarkCheck size={14} /> : <Bookmark size={14} />}
        </button>

        {/* Match score circle (top-right, below save) */}
        {matchScore != null && fit && (
          <div className="absolute top-14 right-3 flex flex-col items-center">
            <div className="relative w-12 h-12">
              <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
                <circle cx="18" cy="18" r="15" fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth="3" />
                <circle
                  cx="18" cy="18" r="15" fill="none"
                  className="stroke-white"
                  strokeWidth="3"
                  strokeDasharray={`${matchScore * 0.942} 100`}
                  strokeLinecap="round"
                />
              </svg>
              <span className="absolute inset-0 flex items-center justify-center text-[11px] font-bold text-white">
                {matchScore}%
              </span>
            </div>
          </div>
        )}

        {/* Main header content */}
        <div className="relative flex items-start gap-3">
          {/* Degree monogram tile */}
          <div className={`flex-shrink-0 w-14 h-14 rounded-xl bg-white/95 ring-2 ${theme.ring} flex flex-col items-center justify-center shadow-sm`}>
            <GraduationCap size={14} className={theme.chipText} />
            <span className={`text-[10px] font-black tracking-wide ${theme.chipText} leading-none mt-0.5`}>
              {abbrev}
            </span>
          </div>

          {/* Title block */}
          <div className="min-w-0 flex-1 pr-10">
            <h3 className="text-[15px] font-bold text-white leading-tight line-clamp-2 drop-shadow-sm">
              {program.program_name}
            </h3>
            {(program.department || program.institution_name) && (
              <p className="text-[11px] text-white/80 mt-1 truncate">
                {program.department || program.institution_name}
                {program.department && program.institution_city && (
                  <span className="text-white/50"> · {program.institution_city}</span>
                )}
              </p>
            )}
          </div>
        </div>

        {/* Degree label + fit chip */}
        <div className="relative flex items-center gap-1.5 mt-3 flex-wrap">
          <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-md bg-white/95 text-slate-800">
            {degree}
          </span>
          {fit && (
            <span className={`px-2 py-0.5 text-[10px] font-bold rounded-md bg-white/95 ${fit.pill.split(' ')[1]}`}>
              {fit.text}
            </span>
          )}
        </div>
      </div>

      {/* ── Meta pills row ── */}
      {metaItems.length > 0 && (
        <div className="flex items-center gap-1.5 px-4 py-2 border-b border-divider bg-slate-50/50 overflow-x-auto">
          {duration && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-white border border-slate-200 text-[10px] text-slate-700 whitespace-nowrap">
              <Clock size={10} className="text-slate-400" />
              {duration}
            </span>
          )}
          {format && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-white border border-slate-200 text-[10px] text-slate-700 whitespace-nowrap">
              <Building size={10} className="text-slate-400" />
              {format}
            </span>
          )}
          {deadline && !deadline.closed && (
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border text-[10px] whitespace-nowrap ${
              deadline.urgent
                ? 'bg-amber-50 border-amber-200 text-amber-700 font-semibold'
                : 'bg-white border-slate-200 text-slate-700'
            }`}>
              <Calendar size={10} className={deadline.urgent ? 'text-amber-500' : 'text-slate-400'} />
              {deadline.urgent ? `Deadline ${deadline.text}` : deadline.text}
            </span>
          )}
        </div>
      )}

      {/* ── Description ── */}
      <div className="flex-1 px-4 pt-3 cursor-pointer" onClick={onView}>
        {program.description_text ? (
          <p className="text-[12px] text-student-text leading-relaxed line-clamp-3">
            {program.description_text.replace(/\s*\[Source:.*?\]\s*/g, '').trim()}
          </p>
        ) : (
          <p className="text-[11px] text-student-text/50 italic">
            No description available — click to view full program details.
          </p>
        )}
      </div>

      {/* ── Stats grid (2×2, colored by tone) ── */}
      <div className="px-4 pt-3 pb-3 grid grid-cols-2 gap-1.5">
        {/* Acceptance */}
        <StatTile
          label="Acceptance"
          value={acceptPct != null ? `${acceptPct}%` : '—'}
          icon={Percent}
          tone="amber"
          emphasize={acceptPct != null && acceptPct < 20}
        />
        {/* Tuition */}
        <StatTile
          label="Tuition / yr"
          value={program.tuition != null ? formatCurrency(program.tuition) : '—'}
          icon={DollarSign}
          tone="rose"
        />
        {/* Salary */}
        <StatTile
          label="Avg Salary"
          value={program.median_salary != null ? formatCurrency(program.median_salary) : '—'}
          icon={TrendingUp}
          tone="emerald"
          emphasize={program.median_salary != null && program.median_salary > 80000}
        />
        {/* Grad rate */}
        <StatTile
          label="Grad Rate"
          value={gradPct != null ? `${gradPct}%` : '—'}
          icon={GraduationCap}
          tone="blue"
          emphasize={gradPct != null && gradPct > 85}
        />
      </div>

      {/* ── Actions ── */}
      <div className="flex items-stretch border-t border-divider mt-auto">
        {onCompare && (
          <button
            onClick={e => { e.stopPropagation(); onCompare() }}
            className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 text-[11px] font-medium transition-colors border-r border-divider ${
              comparing
                ? 'text-student bg-student-mist'
                : 'text-student-text hover:bg-slate-50 hover:text-student-ink'
            }`}
            title={comparing ? 'In compare tray' : 'Add to compare'}
          >
            <ArrowRightLeft size={12} />
            <span className="hidden sm:inline">Compare</span>
          </button>
        )}
        {onAskCounselor && (
          <button
            onClick={e => { e.stopPropagation(); onAskCounselor() }}
            className="flex-1 flex items-center justify-center gap-1.5 py-2.5 text-[11px] font-medium text-gold hover:bg-gold-soft/50 transition-colors border-r border-divider"
            title="Ask your AI counselor about this program"
          >
            <Sparkles size={12} />
            <span className="hidden sm:inline">Ask AI</span>
          </button>
        )}
        <button
          onClick={e => { e.stopPropagation(); onView() }}
          className="flex-[1.5] flex items-center justify-center gap-1.5 py-2.5 text-[11px] font-semibold text-white bg-student hover:bg-student-hover transition-colors group/view"
        >
          View Program
          <ArrowRight size={12} className="group-hover/view:translate-x-0.5 transition-transform" />
        </button>
      </div>
    </div>
  )
}

/* ── Stat tile sub-component ── */

const TONE_STYLES = {
  amber: {
    bg: 'bg-amber-50/60',
    emphasizeBg: 'bg-amber-100',
    border: 'border-amber-100',
    emphasizeBorder: 'border-amber-300',
    icon: 'text-amber-600',
    value: 'text-amber-900',
    label: 'text-amber-700/80',
  },
  rose: {
    bg: 'bg-rose-50/60',
    emphasizeBg: 'bg-rose-100',
    border: 'border-rose-100',
    emphasizeBorder: 'border-rose-300',
    icon: 'text-rose-600',
    value: 'text-rose-900',
    label: 'text-rose-700/80',
  },
  emerald: {
    bg: 'bg-emerald-50/60',
    emphasizeBg: 'bg-emerald-100',
    border: 'border-emerald-100',
    emphasizeBorder: 'border-emerald-300',
    icon: 'text-emerald-600',
    value: 'text-emerald-900',
    label: 'text-emerald-700/80',
  },
  blue: {
    bg: 'bg-blue-50/60',
    emphasizeBg: 'bg-blue-100',
    border: 'border-blue-100',
    emphasizeBorder: 'border-blue-300',
    icon: 'text-blue-600',
    value: 'text-blue-900',
    label: 'text-blue-700/80',
  },
} as const

interface StatTileProps {
  label: string
  value: string
  icon: typeof DollarSign
  tone: keyof typeof TONE_STYLES
  emphasize?: boolean
}

function StatTile({ label, value, icon: Icon, tone, emphasize }: StatTileProps) {
  const styles = TONE_STYLES[tone]
  const isEmpty = value === '—'
  return (
    <div
      className={`flex items-center gap-2 px-2.5 py-2 rounded-lg border transition-colors ${
        isEmpty
          ? 'bg-slate-50 border-slate-100'
          : emphasize
            ? `${styles.emphasizeBg} ${styles.emphasizeBorder}`
            : `${styles.bg} ${styles.border}`
      }`}
    >
      <div className={`w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0 ${
        isEmpty ? 'bg-white' : 'bg-white/80'
      }`}>
        <Icon size={11} className={isEmpty ? 'text-slate-300' : styles.icon} />
      </div>
      <div className="min-w-0">
        <p className={`text-[9px] uppercase tracking-wide leading-none ${
          isEmpty ? 'text-slate-400' : styles.label
        }`}>
          {label}
        </p>
        <p className={`text-[13px] font-bold leading-tight truncate mt-0.5 ${
          isEmpty ? 'text-slate-300' : styles.value
        }`}>
          {value}
        </p>
      </div>
    </div>
  )
}
