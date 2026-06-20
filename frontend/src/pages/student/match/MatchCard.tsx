/**
 * Spec 09 §4 — Match-result card.
 *
 * The canonical display card (Spec 02 §5) in a match context: DualRing
 * (outer fitness / inner confidence, Spec 09 §10), reach/target/safer band
 * badge (§6), a "Why this match" trigger that opens the AI Rationale Popover
 * (§4 / Spec 02 §6), and expandable probability bands (§4A).
 *
 * Brand (§10 / Spec 76): gold appears ONLY on the DualRing fitness ring; the
 * card body is cobalt + neutral, using semantic tokens (dark-mode safe).
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
  Users,
} from 'lucide-react'

import { DEGREE_LABELS } from '../../../utils/constants'
import { formatCurrency } from '../../../utils/format'
import BandBadge from '../../../components/ui/BandBadge'
import type { MatchResultDual } from '../../../types'
import DualRing from './DualRing'
import ProbabilityBands from './ProbabilityBands'
import RationalePopover from './RationalePopover'
import { cardLinkClick } from '../explore/shared/cardLink'
import { ringFromMatch } from './ringFill'
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
  /** Discover review 2026-06-14 #5 — k-anonymized count of peers open to connect. */
  peerCount?: number
  onPeersClick?: () => void
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
  peerCount,
  onPeersClick,
  appStatus,
}: MatchCardProps) {
  const [rationaleOpen, setRationaleOpen] = useState(false)
  const [showBands, setShowBands] = useState(false)
  // Ship D §4 — the program title + View CTA are real links so keyboard
  // focus, Enter, and cmd/ctrl-click open-in-new-tab work.
  const href = `/s/programs/${match.program_id}`

  const degree = match.degree_type ? DEGREE_LABELS[match.degree_type] ?? match.degree_type : null
  const fitRing = ringFromMatch(match.fitness_score, match.band_label)
  const confRing = ringFromMatch(match.confidence_score, match.band_label)
  const fitness = fitRing.value
  const confidence = confRing.value
  // Hide the precise numeral when the ring is band-derived (no raw score served).
  const hideNumeral = fitRing.fromBand
  const acceptPct =
    match.acceptance_rate != null ? Math.round(match.acceptance_rate * 100) : null
  // Without an explicit reason on the list payload, derive the right "not
  // enough data yet" copy from whether the program has a historical rate.
  const bandsReason = match.acceptance_rate == null ? 'no_history' : 'not_match_ready'

  return (
    <div className="bg-card rounded-xl border border-border elev-subtle flex flex-col overflow-hidden hover-lift hover:elev-raised">
      {/* ── Header ── */}
      <div className="p-4 flex items-start gap-3">
        <DualRing fitness={fitness} confidence={confidence} size={72} compact bandLabel={match.band_label ?? undefined} hideNumeral={hideNumeral} onClick={() => setRationaleOpen(true)} />
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
            {match.tuition != null && (
              <span className="text-[11px] text-muted-foreground">{formatCurrency(match.tuition)}/yr</span>
            )}
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
            {peerCount != null && peerCount > 0 && (
              <button
                onClick={e => { e.stopPropagation(); onPeersClick?.() }}
                className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-medium rounded-md bg-secondary/10 text-secondary hover:bg-secondary/20 transition-colors"
                title="Peers open to connect who are applying here"
              >
                <Users size={10} />
                {peerCount} open to connect
              </button>
            )}
          </div>
        </div>
      </div>

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
          confidenceScore={confidence}
          cachedRationale={match.rationale_text}
          onClose={() => setRationaleOpen(false)}
        />
      )}
    </div>
  )
}
