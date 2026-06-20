import type { ComponentType } from 'react'
import { Link } from 'react-router-dom'
import { formatCurrency } from '../../../../utils/format'
import type { ProgramSummary, MatchResult } from '../../../../types'
import {
  BellPlus, BellRing, Bookmark, BookmarkCheck, CalendarDays, DollarSign, GraduationCap,
  TrendingUp, Percent, ArrowRightLeft,
  Clock, Building, Calendar, ArrowRight, Sparkles, Users,
} from 'lucide-react'
import BandBadge from '../../../../components/ui/BandBadge'
import type { Band } from '../../../../components/ui/BandBadge'
import DualRing from '../../match/DualRing'
import { ringFromMatch } from '../../match/ringFill'
import AppStatusPill, { type AppStatus } from './AppStatusPill'
import { cardLinkClick, CARD_LINK_OVERLAY } from '../shared/cardLink'
import { degreeAbbrev, formatDuration, formatFormat, deadlineInfo } from './programFormat'

interface Props {
  program: ProgramSummary
  saved: boolean
  match?: MatchResult
  comparing?: boolean
  onSave: () => void
  onCompare?: () => void
  onAskCounselor?: () => void
  onView: () => void
  /** Spec 2026-06-12 §6.1 — follow the program's institution for updates. */
  following?: boolean
  onToggleFollow?: () => void
  /** Spec 2026-06-12 §6.4 — next upcoming event from this school. */
  nextEvent?: { event_name: string; start_time: string } | null
  onEventClick?: () => void
  /** Discover review 2026-06-14 #5 — k-anonymized count of peers open to connect. */
  peerCount?: number
  onPeersClick?: () => void
  /** Discover review 2026-06-19 — real application stage for this program, if any. */
  appStatus?: AppStatus | null
  /** Ship D §4 — real link destination for the card. Defaults to the student
      program route; public-capable callers pass their auth-aware path. */
  viewHref?: string
}

export default function ProgramCard({ program, saved, match, comparing, onSave, onCompare, onAskCounselor, onView, following, onToggleFollow, nextEvent, onEventClick, peerCount, onPeersClick, appStatus, viewHref }: Props) {
  const abbrev = degreeAbbrev(program.degree_type)
  const href = viewHref ?? `/s/programs/${program.id}`
  // Dual-score migration: prefer fitness_score, fall back to legacy match_score
  // (Phase E keeps match_score dual-written for one release — see CLAUDE.md).
  const extMatch = match as (MatchResult & { fitness_score?: number | null; confidence_score?: number | null; band_label?: string | null }) | undefined
  const fitnessRaw = extMatch?.fitness_score ?? match?.match_score
  const confidenceRaw = extMatch?.confidence_score
  const bandLabel = extMatch?.band_label as Band | undefined
  // Mirror MatchCard (AI-Structure-3 §14): use a raw score if served, else map
  // the band to a representative ring fill and hide the precise numeral — so the
  // program card and the match card never disagree on what's knowable.
  const fitRing = ringFromMatch(fitnessRaw, bandLabel)
  const confRing = ringFromMatch(confidenceRaw, bandLabel)
  const fitness = fitRing.value
  const confidence = confRing.value
  const hideNumeral = fitRing.fromBand
  const hasRing = fitnessRaw != null || !!bandLabel

  const duration = formatDuration(program.duration_months)
  const format = formatFormat(program.delivery_format)
  const deadline = deadlineInfo(program.application_deadline)

  const acceptPct = program.acceptance_rate != null ? Math.round(program.acceptance_rate * 100) : null
  const gradPct = program.employment_rate != null ? Math.round(program.employment_rate * 100) : null

  return (
    <div className="h-full bg-card rounded-xl border border-border elev-subtle hover-lift hover:elev-raised overflow-hidden flex flex-col group/card">
      {/* ── Header — text-driven, white surface, hairline divider. The title
          <Link> stretches over the header (Ship D §4) so keyboard focus,
          Enter, and cmd/ctrl-click work; action buttons stay siblings raised
          above the overlay (no nested-interactive). ── */}
      <div className="relative px-4 pt-4 pb-3 border-b border-border">
        {/* Save button */}
        <button
          onClick={e => { e.preventDefault(); e.stopPropagation(); onSave() }}
          className={`absolute z-10 top-3 right-3 p-2 rounded-full transition-colors ${
            saved ? 'text-secondary bg-secondary/10' : 'text-muted-foreground hover:bg-muted'
          }`}
          aria-label={saved ? 'Remove from list' : 'Save to my list'}
        >
          {saved ? <BookmarkCheck size={15} /> : <Bookmark size={15} />}
        </button>

        {/* Follow-school button (Spec 2026-06-12 §6.1) — updates land in Discover. */}
        {onToggleFollow && (
          <button
            onClick={e => { e.preventDefault(); e.stopPropagation(); onToggleFollow() }}
            className={`absolute z-10 top-3 right-12 p-2 rounded-full transition-colors ${
              following ? 'text-secondary bg-secondary/10' : 'text-muted-foreground hover:bg-muted'
            }`}
            aria-label={following ? `Unfollow ${program.institution_name}` : `Follow ${program.institution_name} for updates`}
            title={following ? `Following ${program.institution_name}` : `Follow ${program.institution_name}`}
          >
            {following ? <BellRing size={15} /> : <BellPlus size={15} />}
          </button>
        )}

        <div className={`flex items-start gap-3 ${onToggleFollow ? 'pr-[4.5rem]' : 'pr-9'}`}>
          {/* Degree monogram tile — muted surface, cobalt mark (no gradient). */}
          <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-muted border border-border/60 flex flex-col items-center justify-center">
            <GraduationCap size={13} className="text-secondary" />
            <span className="text-[10px] font-bold tracking-wide text-secondary leading-none mt-0.5">{abbrev}</span>
          </div>

          <div className="min-w-0 flex-1">
            {/* Fixed 2-line height so the header divider lines up across cards. */}
            <h3 className="text-[15px] font-bold text-foreground leading-tight line-clamp-2 min-h-[2.35rem]">
              <Link to={href} onClick={cardLinkClick(onView)} className={CARD_LINK_OVERLAY}>
                {program.program_name}
              </Link>
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

        {/* Band / match-ring / event row — only when there's something to show.
            The degree is already conveyed by the monogram tile and the full
            program name, so no separate degree chip here. */}
        {(hasRing || nextEvent || (peerCount != null && peerCount > 0) || appStatus) && (
          <div className="flex items-center gap-1.5 mt-3 flex-wrap">
            <AppStatusPill status={appStatus} />
            {bandLabel && <BandBadge band={bandLabel} />}
            {nextEvent && (
              <button
                onClick={e => { e.preventDefault(); e.stopPropagation(); onEventClick?.() }}
                className="relative z-10 inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-medium rounded-md bg-secondary/10 text-secondary hover:bg-secondary/20 transition-colors"
                title={`Upcoming: ${nextEvent.event_name}`}
              >
                <CalendarDays size={10} />
                {nextEvent.event_name.length > 18 ? nextEvent.event_name.slice(0, 18) + '…' : nextEvent.event_name} ·{' '}
                {new Date(nextEvent.start_time).toLocaleDateString('en-US', { weekday: 'short' })}
              </button>
            )}
            {peerCount != null && peerCount > 0 && (
              <button
                onClick={e => { e.preventDefault(); e.stopPropagation(); onPeersClick?.() }}
                className="relative z-10 inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-medium rounded-md bg-secondary/10 text-secondary hover:bg-secondary/20 transition-colors"
                title="Peers open to connect who are applying here"
              >
                <Users size={10} />
                {peerCount} open to connect
              </button>
            )}
            {hasRing && (
              <span className="ml-auto">
                <DualRing
                  fitness={fitness}
                  confidence={confidence}
                  size={40}
                  compact
                  bandLabel={bandLabel}
                  hideNumeral={hideNumeral}
                />
              </span>
            )}
          </div>
        )}
      </div>

      {/* ── Facts grid — one consistent block on every card. Duration + format
          are almost always present, so even programs without numeric outcomes
          (e.g. non-degree certificates) keep a populated, uniform layout rather
          than collapsing to a bare description. ── */}
      {(() => {
        const tiles: { label: string; value: string; icon: typeof Percent; urgent?: boolean }[] = []
        if (duration) tiles.push({ label: 'Duration', value: duration, icon: Clock })
        if (format) tiles.push({ label: 'Format', value: format, icon: Building })
        if (deadline && !deadline.closed)
          tiles.push({ label: 'Deadline', value: deadline.text, icon: Calendar, urgent: deadline.urgent })
        if (acceptPct != null) tiles.push({ label: 'Acceptance', value: `${acceptPct}%`, icon: Percent })
        if (program.tuition != null)
          tiles.push({ label: 'Tuition / yr', value: program.tuition === 0 ? 'Funded' : formatCurrency(program.tuition), icon: DollarSign })
        if (program.median_salary != null)
          tiles.push({ label: 'Avg salary', value: formatCurrency(program.median_salary), icon: TrendingUp })
        if (gradPct != null) tiles.push({ label: 'Grad rate', value: `${gradPct}%`, icon: GraduationCap })
        if (!tiles.length) return null
        return (
          <div className="px-4 pt-3 grid grid-cols-2 gap-1.5">
            {tiles.map(t => (
              <StatTile key={t.label} label={t.label} value={t.value} icon={t.icon} urgent={t.urgent} />
            ))}
          </div>
        )
      })()}

      {/* ── Description — the flexible filler so every card's footer pins to the
          bottom and the grid stays even regardless of how much data a card has ── */}
      <div className="flex-1 px-4 pt-3 pb-1 cursor-pointer" onClick={onView}>
        {program.description_text ? (
          <p className="text-[12px] text-muted-foreground leading-relaxed line-clamp-3">
            {program.description_text.replace(/\s*\[Source:.*?\]\s*/g, '').trim()}
          </p>
        ) : (
          <p className="text-[11px] text-muted-foreground/60 italic">No description available.</p>
        )}
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
        <Link
          to={href}
          onClick={cardLinkClick(onView)}
          className="flex-[1.5] flex items-center justify-center gap-1.5 py-2.5 text-[11px] font-semibold text-secondary-foreground bg-secondary hover:brightness-95 transition-colors group/view"
        >
          View program
          <ArrowRight size={12} className="group-hover/view:translate-x-0.5 transition-transform" />
        </Link>
      </div>
    </div>
  )
}

/* ── Stat tile (neutral editorial; warning tone for an urgent deadline) ── */
interface StatTileProps {
  label: string
  value: string
  icon: ComponentType<{ size?: number; className?: string }>
  urgent?: boolean
}

function StatTile({ label, value, icon: Icon, urgent }: StatTileProps) {
  return (
    <div className={`flex items-center gap-2 px-2.5 py-2 rounded-md border ${urgent ? 'bg-warning-soft border-warning/40' : 'bg-muted/60 border-border/60'}`}>
      <div className={`w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0 bg-card border ${urgent ? 'border-warning/30' : 'border-border/50'}`}>
        <Icon size={11} className={urgent ? 'text-warning' : 'text-secondary'} />
      </div>
      <div className="min-w-0">
        <p className={`text-[9px] uppercase tracking-wide leading-none ${urgent ? 'text-warning' : 'text-muted-foreground'}`}>{label}</p>
        <p className={`text-[13px] font-bold leading-tight truncate mt-0.5 ${urgent ? 'text-warning' : 'text-foreground'}`}>{value}</p>
      </div>
    </div>
  )
}
