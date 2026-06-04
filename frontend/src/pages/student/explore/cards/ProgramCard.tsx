import type { ComponentType } from 'react'
import { formatCurrency } from '../../../../utils/format'
import { DEGREE_LABELS } from '../../../../utils/constants'
import type { ProgramSummary, MatchResult } from '../../../../types'
import {
  Bookmark, BookmarkCheck, DollarSign, GraduationCap,
  TrendingUp, Percent, ArrowRightLeft,
  Clock, Building, Calendar, ArrowRight, Sparkles,
} from 'lucide-react'
import { differenceInDays } from 'date-fns'

// Band label from match tier — editorial duotone, no rainbow (Spec/02 §9).
function fitStyle(tier: number) {
  if (tier >= 3) return { text: 'Strong fit', pill: 'bg-success-soft text-success border-success/30' }
  if (tier >= 2) return { text: 'Good fit', pill: 'bg-secondary/10 text-secondary border-secondary/30' }
  return { text: 'Reach', pill: 'bg-card text-secondary border-secondary/50' }
}

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
    on_campus: 'On campus', online: 'Online',
    hybrid: 'Hybrid', in_person: 'In-person',
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
  const fit = match ? fitStyle(match.match_tier) : null
  // Dual-score migration: prefer fitness_score, fall back to legacy match_score
  // (Phase E keeps match_score dual-written for one release — see CLAUDE.md).
  const rawScore = (match as { fitness_score?: number | null } | undefined)?.fitness_score ?? match?.match_score
  const matchScore = rawScore != null ? Math.round(rawScore * 100) : null

  const duration = formatDuration(program.duration_months)
  const format = formatFormat(program.delivery_format)
  const deadline = deadlineInfo(program.application_deadline)

  const acceptPct = program.acceptance_rate != null ? Math.round(program.acceptance_rate * 100) : null
  const gradPct = program.employment_rate != null ? Math.round(program.employment_rate * 100) : null

  return (
    <div className="bg-card rounded-lg border border-border hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 ease-out overflow-hidden flex flex-col group/card">
      {/* ── Header — text-driven, white surface, hairline divider ── */}
      <div onClick={onView} className="relative cursor-pointer px-4 pt-4 pb-3 border-b border-border">
        {/* Save button */}
        <button
          onClick={e => { e.stopPropagation(); onSave() }}
          className={`absolute top-3 right-3 p-2 rounded-full transition-colors ${
            saved ? 'text-secondary bg-secondary/10' : 'text-muted-foreground hover:bg-muted'
          }`}
          aria-label={saved ? 'Remove from list' : 'Save to my list'}
        >
          {saved ? <BookmarkCheck size={15} /> : <Bookmark size={15} />}
        </button>

        <div className="flex items-start gap-3 pr-9">
          {/* Degree monogram tile — muted surface, cobalt mark (no gradient). */}
          <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-muted border border-border/60 flex flex-col items-center justify-center">
            <GraduationCap size={13} className="text-secondary" />
            <span className="text-[10px] font-bold tracking-wide text-secondary leading-none mt-0.5">{abbrev}</span>
          </div>

          <div className="min-w-0 flex-1">
            <h3 className="text-[15px] font-bold text-foreground leading-tight line-clamp-2">
              {program.program_name}
            </h3>
            {(program.department || program.institution_name) && (
              <p className="text-[11.5px] text-muted-foreground mt-1 truncate flex items-center gap-1">
                <Building size={10} className="flex-shrink-0 text-muted-foreground/70" />
                {program.department || program.institution_name}
                {program.institution_city && <span className="text-muted-foreground/70"> · {program.institution_city}</span>}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-1.5 mt-3 flex-wrap">
          <span className="px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded-md bg-muted text-foreground border border-border/60">
            {degree}
          </span>
          {fit && (
            <span className={`px-2 py-0.5 text-[10px] font-semibold rounded-md border ${fit.pill}`}>
              {fit.text}
            </span>
          )}
          {matchScore != null && (
            <span className="ml-auto inline-flex items-center gap-1.5">
              <MatchDot pct={matchScore} />
              <span className="text-[11px] font-bold text-foreground">{matchScore}<span className="text-muted-foreground font-normal">% fit</span></span>
            </span>
          )}
        </div>
      </div>

      {/* ── Meta pills row ── */}
      {(duration || format || (deadline && !deadline.closed)) && (
        <div className="flex items-center gap-1.5 px-4 py-2 border-b border-border bg-muted/40 overflow-x-auto">
          {duration && <MetaPill icon={Clock}>{duration}</MetaPill>}
          {format && <MetaPill icon={Building}>{format}</MetaPill>}
          {deadline && !deadline.closed && (
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border text-[10px] whitespace-nowrap ${
              deadline.urgent ? 'bg-warning-soft border-warning/40 text-warning font-semibold' : 'bg-card border-border/60 text-muted-foreground'
            }`}>
              <Calendar size={10} className={deadline.urgent ? 'text-warning' : 'text-muted-foreground/70'} />
              {deadline.urgent ? `Deadline ${deadline.text}` : deadline.text}
            </span>
          )}
        </div>
      )}

      {/* ── Description ── */}
      <div className="flex-1 px-4 pt-3 cursor-pointer" onClick={onView}>
        {program.description_text ? (
          <p className="text-[12px] text-muted-foreground leading-relaxed line-clamp-3">
            {program.description_text.replace(/\s*\[Source:.*?\]\s*/g, '').trim()}
          </p>
        ) : (
          <p className="text-[11px] text-muted-foreground/60 italic">No description available — open to view full details.</p>
        )}
      </div>

      {/* ── Stats grid (2×2, neutral editorial tiles) ── */}
      <div className="px-4 pt-3 pb-3 grid grid-cols-2 gap-1.5">
        <StatTile label="Acceptance" value={acceptPct != null ? `${acceptPct}%` : '—'} icon={Percent} />
        <StatTile label="Tuition / yr" value={program.tuition != null ? formatCurrency(program.tuition) : '—'} icon={DollarSign} />
        <StatTile label="Avg salary" value={program.median_salary != null ? formatCurrency(program.median_salary) : '—'} icon={TrendingUp} />
        <StatTile label="Grad rate" value={gradPct != null ? `${gradPct}%` : '—'} icon={GraduationCap} />
      </div>

      {/* ── Actions ── */}
      <div className="flex items-stretch border-t border-border mt-auto">
        {onCompare && (
          <button
            onClick={e => { e.stopPropagation(); onCompare() }}
            className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 text-[11px] font-medium transition-colors border-r border-border ${
              comparing ? 'text-secondary bg-secondary/10' : 'text-muted-foreground hover:bg-muted hover:text-foreground'
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
            className="flex-1 flex items-center justify-center gap-1.5 py-2.5 text-[11px] font-medium text-secondary hover:bg-secondary/5 transition-colors border-r border-border"
            title="Ask your AI counselor about this program"
          >
            <Sparkles size={12} />
            <span className="hidden sm:inline">Ask AI</span>
          </button>
        )}
        <button
          onClick={e => { e.stopPropagation(); onView() }}
          className="flex-[1.5] flex items-center justify-center gap-1.5 py-2.5 text-[11px] font-semibold text-secondary-foreground bg-secondary hover:brightness-95 transition-colors group/view"
        >
          View program
          <ArrowRight size={12} className="group-hover/view:translate-x-0.5 transition-transform" />
        </button>
      </div>
    </div>
  )
}

/* ── Small gold match dot (the one earned accent on the card) ── */
function MatchDot({ pct }: { pct: number }) {
  const r = 9
  const c = 2 * Math.PI * r
  return (
    <span className="relative inline-flex w-5 h-5">
      <svg viewBox="0 0 24 24" className="w-5 h-5 -rotate-90">
        <circle cx="12" cy="12" r={r} fill="none" className="stroke-border/50" strokeWidth="3" />
        <circle
          cx="12" cy="12" r={r} fill="none"
          className="stroke-primary" strokeWidth="3" strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={c * (1 - pct / 100)}
        />
      </svg>
    </span>
  )
}

/* ── Meta pill ── */
function MetaPill({ icon: Icon, children }: { icon: ComponentType<{ size?: number; className?: string }>; children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-card border border-border/60 text-[10px] text-muted-foreground whitespace-nowrap">
      <Icon size={10} className="text-muted-foreground/70" />
      {children}
    </span>
  )
}

/* ── Stat tile (neutral editorial) ── */
interface StatTileProps {
  label: string
  value: string
  icon: ComponentType<{ size?: number; className?: string }>
}

function StatTile({ label, value, icon: Icon }: StatTileProps) {
  const isEmpty = value === '—'
  return (
    <div className={`flex items-center gap-2 px-2.5 py-2 rounded-md border ${isEmpty ? 'bg-muted/40 border-border/40' : 'bg-muted/60 border-border/60'}`}>
      <div className="w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0 bg-card border border-border/50">
        <Icon size={11} className={isEmpty ? 'text-muted-foreground/40' : 'text-secondary'} />
      </div>
      <div className="min-w-0">
        <p className={`text-[9px] uppercase tracking-wide leading-none ${isEmpty ? 'text-muted-foreground/40' : 'text-muted-foreground'}`}>{label}</p>
        <p className={`text-[13px] font-bold leading-tight truncate mt-0.5 ${isEmpty ? 'text-muted-foreground/40' : 'text-foreground'}`}>{value}</p>
      </div>
    </div>
  )
}
