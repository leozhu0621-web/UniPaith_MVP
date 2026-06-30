/**
 * Spec 09 §4 — Match-result card.
 *
 * The canonical display card (Spec 02 §5) in a match context: a reach/target/
 * safer band badge (§6), the one-line counselor storyline, a "Why this match"
 * trigger that opens the AI Rationale Popover (§4 / Spec 02 §6), and expandable
 * probability bands (§4A). The fitness/confidence score rings were dropped to
 * keep the card simple — the band + storyline carry the read now.
 * Save / Add to compare / Open on every card (§7).
 */
import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowRight,
  Bookmark,
  BookmarkCheck,
  ArrowRightLeft,
  CalendarDays,
  ChevronDown,
  Sparkles,
} from 'lucide-react'

import { degreeAbbrev } from '../explore/cards/programFormat'
import { formatCurrency } from '../../../utils/format'
import BandBadge from '../../../components/ui/BandBadge'
import type { MatchResultDual } from '../../../types'
import { matchStoryline } from './matchStoryline'
import ProbabilityBands from './ProbabilityBands'
import RationalePopover from './RationalePopover'
import { cardLinkClick } from '../explore/shared/cardLink'
import AppStatusPill, { type AppStatus } from '../explore/cards/AppStatusPill'

interface MatchCardProps {
  match: MatchResultDual
  saved: boolean
  comparing: boolean
  onSave: () => void
  onCompare: () => void
  onView: () => void
  /** Spec 2026-06-12 §6.4 — next upcoming event from this school (Handshake pattern). */
  nextEvent?: { event_name: string; start_time: string } | null
  onEventClick?: () => void
  /** Discover review 2026-06-19 — real application stage for this program, if any. */
  appStatus?: AppStatus | null
}

export default function MatchCard({
  match,
  saved,
  comparing,
  onSave,
  onCompare,
  onView,
  nextEvent,
  onEventClick,
  appStatus,
}: MatchCardProps) {
  const [rationaleOpen, setRationaleOpen] = useState(false)
  const [showBands, setShowBands] = useState(false)
  // Ship D §4 — the program title + View CTA are real links so keyboard
  // focus, Enter, and cmd/ctrl-click open-in-new-tab work.
  const href = `/s/programs/${match.program_id}`

  const degree = match.degree_type ? degreeAbbrev(match.degree_type, match.program_name ?? undefined) : null
  // Strategy→matches storytelling: a one-line counselor read of this band
  // (band-only — the fitness/confidence score rings were dropped to keep it simple).
  const storyline = matchStoryline(match.band_label, 0, false)
  const acceptPct =
    match.acceptance_rate != null ? Math.round(match.acceptance_rate * 100) : null
  // Affordability readout — net price (after aid) front-and-center, with a budget-fit
  // chip, since money is the student's #1 worry (not sticker tuition).
  const affordMeta: Record<string, { label: string; cls: string }> = {
    affordable: { label: 'Likely under budget', cls: 'bg-secondary/10 text-secondary' },
    stretch: { label: 'A stretch on budget', cls: 'bg-muted text-foreground' },
    out_of_reach: { label: 'Over budget', cls: 'bg-error/10 text-error' },
  }
  const affordInfo = match.affordability_band ? affordMeta[match.affordability_band] : undefined
  // Without an explicit reason on the list payload, derive the right "not
  // enough data yet" copy from whether the program has a historical rate.
  const bandsReason = match.acceptance_rate == null ? 'no_history' : 'not_match_ready'

  return (
    <div className="bg-card rounded-xl border border-border elev-subtle flex flex-col overflow-hidden hover-lift hover:elev-raised">
      {/* ── Header ── */}
      <div className="p-4 flex items-start gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <Link to={href} onClick={cardLinkClick(onView)} className="min-w-0 text-left">
              <h3 className="text-[15px] font-bold text-foreground leading-tight line-clamp-2 break-words hover:text-secondary transition-colors">
                {match.program_name ?? 'Program'}
              </h3>
              {match.institution_name && (
                <p className="text-[12px] text-muted-foreground mt-0.5 truncate">{match.institution_name}</p>
              )}
            </Link>
            <button
              onClick={onSave}
              className={`shrink-0 p-1.5 rounded-full transition-colors ${
                saved ? 'text-secondary bg-secondary/10' : 'text-muted-foreground hover:bg-muted'
              }`}
              aria-label={saved ? 'Remove from list' : 'Save to my list'}
            >
              {saved ? <BookmarkCheck size={15} /> : <Bookmark size={15} />}
            </button>
          </div>

          <div className="flex items-center gap-1.5 mt-2 flex-wrap">
            <AppStatusPill status={appStatus} />
            {match.band_label && <BandBadge band={match.band_label} />}
            {degree && (
              <span className="px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded-md bg-muted text-foreground border border-border/60">
                {degree}
              </span>
            )}
            {affordInfo && (
              <span
                className={`inline-flex items-center px-2 py-0.5 text-[10px] font-semibold rounded-md ${affordInfo.cls}`}
                title="Estimated yearly net price after typical aid — your budget fit, not sticker tuition"
              >
                {affordInfo.label}
              </span>
            )}
            {match.net_price_annual != null ? (
              <span className="text-[11px] text-muted-foreground">~{formatCurrency(match.net_price_annual)}/yr after aid</span>
            ) : match.tuition != null ? (
              <span className="text-[11px] text-muted-foreground">{formatCurrency(match.tuition)}/yr</span>
            ) : null}
            {acceptPct != null && (
              <span className="text-[11px] text-muted-foreground">· {acceptPct}% admit</span>
            )}
            {nextEvent && (
              <button
                onClick={e => { e.stopPropagation(); onEventClick?.() }}
                className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-medium rounded-md bg-secondary/10 text-secondary hover:bg-secondary/20 transition-colors"
                title={`Upcoming: ${nextEvent.event_name}`}
              >
                <CalendarDays size={10} />
                {nextEvent.event_name.length > 18 ? nextEvent.event_name.slice(0, 18) + '…' : nextEvent.event_name} ·{' '}
                {new Date(nextEvent.start_time).toLocaleDateString('en-US', { weekday: 'short' })}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* ── Band storyline — the counselor's one-line read (fit + odds) ── */}
      {storyline && (
        <p className="px-4 -mt-0.5 pb-1.5 text-[12.5px] leading-snug text-foreground/85">
          {storyline}
        </p>
      )}

      {/* ── Why this match + realistic-shot expander ── */}
      <div className="px-4 pb-2 flex items-center gap-3">
        <button
          onClick={() => setRationaleOpen(true)}
          className="inline-flex items-center gap-1 text-xs font-semibold text-secondary hover:underline"
        >
          <Sparkles size={12} /> Why this match
        </button>
        <button
          onClick={() => setShowBands(v => !v)}
          className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground ml-auto"
          aria-expanded={showBands}
        >
          Your realistic shot
          <ChevronDown size={13} className={`transition-transform ${showBands ? 'rotate-180' : ''}`} />
        </button>
      </div>

      {showBands && (
        <div className="px-4 pb-3 pt-1 border-t border-border">
          <ProbabilityBands
            bands={match.probability_bands ?? null}
            reason={bandsReason}
            hideHeading
            className="pt-2"
          />
        </div>
      )}

      {/* ── Actions ── */}
      <div className="flex items-stretch border-t border-border mt-auto">
        <button
          onClick={onCompare}
          className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 text-[11px] font-medium transition-colors border-r border-border ${
            comparing ? 'text-secondary bg-secondary/10' : 'text-muted-foreground hover:bg-muted hover:text-foreground'
          }`}
          title={comparing ? 'In compare tray' : 'Add to compare'}
        >
          <ArrowRightLeft size={12} />
          <span className="hidden sm:inline">{comparing ? 'In compare' : 'Compare'}</span>
        </button>
        <Link
          to={href}
          onClick={cardLinkClick(onView)}
          className="flex-[1.5] flex items-center justify-center gap-1.5 py-2.5 text-[11px] font-semibold text-secondary-foreground bg-secondary hover:brightness-95 transition-colors group/view"
        >
          View program
          <ArrowRight size={12} className="group-hover/view:translate-x-0.5 transition-transform" />
        </Link>
      </div>

      {rationaleOpen && (
        <RationalePopover
          programId={match.program_id}
          fitnessBreakdown={match.fitness_breakdown}
          confidenceBreakdown={match.confidence_breakdown}
          cachedRationale={match.rationale_text}
          onClose={() => setRationaleOpen(false)}
        />
      )}
    </div>
  )
}
