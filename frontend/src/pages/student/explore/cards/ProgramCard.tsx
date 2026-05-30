import { formatCurrency } from '../../../../utils/format'
import { DEGREE_LABELS } from '../../../../utils/constants'
import type { ProgramSummary, MatchResult } from '../../../../types'
import { parseScore } from '../../../../types'
import DualRing from '../../match/DualRing'
import {
  Bookmark, BookmarkCheck, DollarSign, GraduationCap,
  TrendingUp, Percent, ArrowRightLeft,
  Clock, Building, Calendar, ArrowRight, Sparkles,
} from 'lucide-react'
import { differenceInDays } from 'date-fns'

/**
 * Editorial program card — Europa + Paper + Cobalt/Gold accents.
 *
 * No technicolor gradients; degree is encoded in a small lettered chip
 * + a cobalt left-edge strip (gold for "target" fit). Match scoring
 * prefers the dual-score (fitness + confidence) fields and renders the
 * shared DualRing so the surface matches the program detail page.
 */
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

/**
 * Resolve dual-score (fitness + confidence) from either the new or legacy
 * MatchResult shape. Falls back to legacy match_score for fitness if the
 * server hasn't migrated; in that case confidence is fixed at 0.6 ("medium")
 * so the inner ring reads as "we'd like more signal" rather than guessing.
 */
function resolveScores(match?: MatchResult): { fitness: number; confidence: number } | null {
  if (!match) return null
  const fitness = parseScore(match.fitness_score) ?? parseScore(match.match_score)
  if (fitness == null) return null
  const confidence = parseScore(match.confidence_score) ?? 0.6
  return { fitness, confidence }
}

function fitChip(fitness: number): { label: string; tone: 'gold' | 'cobalt' | 'warning' | 'error' } {
  if (fitness >= 0.85) return { label: 'Strong Fit', tone: 'gold' }
  if (fitness >= 0.7) return { label: 'Good Fit', tone: 'cobalt' }
  if (fitness >= 0.5) return { label: 'Stretch', tone: 'warning' }
  return { label: 'Reach', tone: 'error' }
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
  const scores = resolveScores(match)
  const chip = scores ? fitChip(scores.fitness) : null

  const duration = formatDuration(program.duration_months)
  const format = formatFormat(program.delivery_format)
  const deadline = deadlineInfo(program.application_deadline)

  const acceptPct = program.acceptance_rate != null ? Math.round(program.acceptance_rate * 100) : null
  const gradPct = program.employment_rate != null ? Math.round(program.employment_rate * 100) : null

  const accentClass = chip?.tone === 'gold'
    ? 'border-l-gold'
    : chip?.tone === 'cobalt'
      ? 'border-l-cobalt'
      : chip?.tone === 'warning'
        ? 'border-l-warning'
        : chip?.tone === 'error'
          ? 'border-l-error'
          : 'border-l-stone'

  const chipClass = chip?.tone === 'gold'
    ? 'bg-gold-soft text-charcoal border-gold/40'
    : chip?.tone === 'cobalt'
      ? 'bg-cobalt/10 text-cobalt border-cobalt/30'
      : chip?.tone === 'warning'
        ? 'bg-warning-soft text-warning border-warning/30'
        : 'bg-error-soft text-error border-error/30'

  return (
    <div className={`bg-white rounded-lg border border-stone/60 hover:shadow-raised hover:-translate-y-0.5 transition-all duration-base ease-brand-out overflow-hidden flex flex-col group/card border-l-4 ${accentClass}`}>
      {/* ── Header (editorial — paper-cream, no decorative imagery) ── */}
      <div
        onClick={onView}
        className="relative cursor-pointer bg-paper px-4 pt-4 pb-3 border-b border-stone/40"
      >
        {/* Save button */}
        <button
          onClick={e => { e.stopPropagation(); onSave() }}
          className={`absolute top-3 right-3 p-1.5 rounded-md transition-all ${
            saved
              ? 'bg-gold text-charcoal'
              : 'bg-white/80 text-slate hover:bg-white hover:text-cobalt border border-stone/60'
          }`}
          aria-label={saved ? 'Unsave program' : 'Save program'}
        >
          {saved ? <BookmarkCheck size={14} /> : <Bookmark size={14} />}
        </button>

        {/* DualRing — top-right, below the save button. */}
        {scores && (
          <div className="absolute top-12 right-3">
            <DualRing
              fitness={scores.fitness}
              confidence={scores.confidence}
              size={56}
              compact
            />
          </div>
        )}

        <div className="flex items-start gap-3 pr-16">
          {/* Degree monogram tile */}
          <div className="flex-shrink-0 w-12 h-12 rounded-md bg-white border border-stone/70 flex flex-col items-center justify-center">
            <GraduationCap size={12} className="text-cobalt" />
            <span className="text-[10px] font-bold tracking-wider text-charcoal leading-none mt-0.5">
              {abbrev}
            </span>
          </div>

          <div className="min-w-0 flex-1">
            <h3 className="text-[15px] font-bold text-charcoal leading-tight line-clamp-2">
              {program.program_name}
            </h3>
            {(program.department || program.institution_name) && (
              <p className="text-[11px] text-slate mt-1 truncate">
                {program.department || program.institution_name}
                {program.department && program.institution_city && (
                  <span className="text-slate/70"> · {program.institution_city}</span>
                )}
              </p>
            )}
          </div>
        </div>

        {/* Degree label + fit chip */}
        <div className="flex items-center gap-1.5 mt-3 flex-wrap">
          <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-sm bg-white text-cobalt border border-cobalt/30">
            {degree}
          </span>
          {chip && (
            <span className={`px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-sm border ${chipClass}`}>
              {chip.label}
            </span>
          )}
        </div>
      </div>

      {/* ── Meta pills row ── */}
      {(duration || format || deadline) && (
        <div className="flex items-center gap-1.5 px-4 py-2 border-b border-stone/40 bg-paper/40 overflow-x-auto">
          {duration && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-sm bg-white border border-stone/60 text-[10px] text-charcoal whitespace-nowrap">
              <Clock size={10} className="text-slate" />
              {duration}
            </span>
          )}
          {format && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-sm bg-white border border-stone/60 text-[10px] text-charcoal whitespace-nowrap">
              <Building size={10} className="text-slate" />
              {format}
            </span>
          )}
          {deadline && !deadline.closed && (
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-sm border text-[10px] whitespace-nowrap ${
              deadline.urgent
                ? 'bg-warning-soft border-warning/30 text-warning font-bold'
                : 'bg-white border-stone/60 text-charcoal'
            }`}>
              <Calendar size={10} className={deadline.urgent ? 'text-warning' : 'text-slate'} />
              {deadline.urgent ? `Deadline ${deadline.text}` : deadline.text}
            </span>
          )}
        </div>
      )}

      {/* ── Description ── */}
      <div className="flex-1 px-4 pt-3 cursor-pointer" onClick={onView}>
        {program.description_text ? (
          <p className="text-[12px] text-slate leading-relaxed line-clamp-3">
            {program.description_text.replace(/\s*\[Source:.*?\]\s*/g, '').trim()}
          </p>
        ) : (
          <p className="text-[11px] text-slate/60 italic">
            No description available — view the full program page.
          </p>
        )}
      </div>

      {/* ── Stats grid (2×2, single neutral tone) ── */}
      <div className="px-4 pt-3 pb-3 grid grid-cols-2 gap-1.5">
        <StatTile
          label="Acceptance"
          value={acceptPct != null ? `${acceptPct}%` : '—'}
          icon={Percent}
          emphasize={acceptPct != null && acceptPct < 20}
        />
        <StatTile
          label="Tuition / yr"
          value={program.tuition != null ? formatCurrency(program.tuition) : '—'}
          icon={DollarSign}
        />
        <StatTile
          label="Avg Salary"
          value={program.median_salary != null ? formatCurrency(program.median_salary) : '—'}
          icon={TrendingUp}
          emphasize={program.median_salary != null && program.median_salary > 80000}
        />
        <StatTile
          label="Grad Rate"
          value={gradPct != null ? `${gradPct}%` : '—'}
          icon={GraduationCap}
          emphasize={gradPct != null && gradPct > 85}
        />
      </div>

      {/* ── Actions ── */}
      <div className="flex items-stretch border-t border-stone/60 mt-auto">
        {onCompare && (
          <button
            onClick={e => { e.stopPropagation(); onCompare() }}
            className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 text-[11px] font-bold transition-colors border-r border-stone/60 ${
              comparing
                ? 'text-cobalt bg-cobalt/10'
                : 'text-slate hover:bg-paper hover:text-charcoal'
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
            className="flex-1 flex items-center justify-center gap-1.5 py-2.5 text-[11px] font-bold text-cobalt hover:bg-cobalt/10 transition-colors border-r border-stone/60"
            title="Ask your AI counselor about this program"
          >
            <Sparkles size={12} />
            <span className="hidden sm:inline">Ask AI</span>
          </button>
        )}
        <button
          onClick={e => { e.stopPropagation(); onView() }}
          className="flex-[1.5] flex items-center justify-center gap-1.5 py-2.5 text-[11px] font-bold text-charcoal bg-gold hover:bg-gold-hover transition-colors group/view"
        >
          View Program
          <ArrowRight size={12} className="group-hover/view:translate-x-0.5 transition-transform" />
        </button>
      </div>
    </div>
  )
}

/* ── Neutral StatTile — single brand tone, emphasizes via paper-cream fill ── */

interface StatTileProps {
  label: string
  value: string
  icon: typeof DollarSign
  emphasize?: boolean
}

function StatTile({ label, value, icon: Icon, emphasize }: StatTileProps) {
  const isEmpty = value === '—'
  return (
    <div
      className={`flex items-center gap-2 px-2.5 py-2 rounded-sm border transition-colors ${
        isEmpty
          ? 'bg-paper/40 border-stone/40'
          : emphasize
            ? 'bg-gold-soft border-gold/40'
            : 'bg-paper border-stone/60'
      }`}
    >
      <div className="w-6 h-6 rounded-sm flex items-center justify-center flex-shrink-0 bg-white border border-stone/40">
        <Icon size={11} className={isEmpty ? 'text-stone' : 'text-cobalt'} />
      </div>
      <div className="min-w-0">
        <p className={`text-[9px] uppercase tracking-wider leading-none ${
          isEmpty ? 'text-stone' : 'text-slate'
        }`}>
          {label}
        </p>
        <p className={`text-[13px] font-bold leading-tight truncate mt-0.5 ${
          isEmpty ? 'text-stone' : 'text-charcoal'
        }`}>
          {value}
        </p>
      </div>
    </div>
  )
}
