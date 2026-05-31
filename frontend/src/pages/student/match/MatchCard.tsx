/**
 * Spec 09 §4 — Match-result card.
 *
 * The canonical display card (Spec 02 §5) in a match context: DualRing
 * (outer fitness / inner confidence, Spec 09 §10), reach/target/safer band
 * badge (§6), a "Why this match" trigger that opens the AI Rationale Popover
 * (§4 / Spec 02 §6), and expandable probability bands (§4A).
 *
 * Brand (§10): gold appears ONLY on the DualRing fitness ring; the card body
 * is cobalt + neutral. Save / Add to compare / Open on every card (§7).
 */
import { useState } from 'react'
import {
  ArrowRight,
  Bookmark,
  BookmarkCheck,
  ArrowRightLeft,
  ChevronDown,
  Sparkles,
} from 'lucide-react'

import { DEGREE_LABELS } from '../../../utils/constants'
import { formatCurrency } from '../../../utils/format'
import BandBadge from '../../../components/ui/BandBadge'
import type { MatchResultDual } from '../../../types'
import DualRing from './DualRing'
import ProbabilityBands from './ProbabilityBands'
import RationalePopover from './RationalePopover'

function toUnit(v: string | number | null | undefined): number {
  const n = typeof v === 'string' ? parseFloat(v) : (v ?? 0)
  if (!Number.isFinite(n)) return 0
  const u = n > 1 ? n / 100 : n
  return Math.max(0, Math.min(1, u))
}

interface MatchCardProps {
  match: MatchResultDual
  saved: boolean
  comparing: boolean
  onSave: () => void
  onCompare: () => void
  onView: () => void
}

export default function MatchCard({
  match,
  saved,
  comparing,
  onSave,
  onCompare,
  onView,
}: MatchCardProps) {
  const [rationaleOpen, setRationaleOpen] = useState(false)
  const [showBands, setShowBands] = useState(false)

  const degree = match.degree_type ? DEGREE_LABELS[match.degree_type] ?? match.degree_type : null
  const fitness = toUnit(match.fitness_score)
  const confidence = toUnit(match.confidence_score)
  const acceptPct =
    match.acceptance_rate != null ? Math.round(match.acceptance_rate * 100) : null
  // Without an explicit reason on the list payload, derive the right "not
  // enough data yet" copy from whether the program has a historical rate.
  const bandsReason = match.acceptance_rate == null ? 'no_history' : 'not_match_ready'

  return (
    <div className="bg-card rounded-xl border border-border elev-subtle flex flex-col overflow-hidden hover:elev-raised transition-shadow">
      {/* ── Header ── */}
      <div className="p-4 flex items-start gap-3">
        <DualRing fitness={fitness} confidence={confidence} size={72} compact onClick={() => setRationaleOpen(true)} />
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <button onClick={onView} className="min-w-0 text-left">
              <h3 className="text-[15px] font-bold text-charcoal leading-tight line-clamp-2 hover:text-cobalt transition-colors">
                {match.program_name ?? 'Program'}
              </h3>
              {match.institution_name && (
                <p className="text-[12px] text-slate mt-0.5 truncate">{match.institution_name}</p>
              )}
            </button>
            <button
              onClick={onSave}
              className={`shrink-0 p-1.5 rounded-full transition-colors ${
                saved ? 'text-cobalt bg-cobalt/10' : 'text-slate hover:bg-muted'
              }`}
              aria-label={saved ? 'Remove from list' : 'Save to my list'}
            >
              {saved ? <BookmarkCheck size={15} /> : <Bookmark size={15} />}
            </button>
          </div>

          <div className="flex items-center gap-1.5 mt-2 flex-wrap">
            {match.band_label && <BandBadge band={match.band_label} />}
            {degree && (
              <span className="px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded-md bg-muted text-charcoal border border-stone/60">
                {degree}
              </span>
            )}
            {match.tuition != null && (
              <span className="text-[11px] text-slate">{formatCurrency(match.tuition)}/yr</span>
            )}
            {acceptPct != null && (
              <span className="text-[11px] text-slate">· {acceptPct}% admit</span>
            )}
          </div>
        </div>
      </div>

      {/* ── Why this match + realistic-shot expander ── */}
      <div className="px-4 pb-2 flex items-center gap-3">
        <button
          onClick={() => setRationaleOpen(true)}
          className="inline-flex items-center gap-1 text-xs font-semibold text-cobalt hover:underline"
        >
          <Sparkles size={12} /> Why this match
        </button>
        <button
          onClick={() => setShowBands(v => !v)}
          className="inline-flex items-center gap-1 text-xs text-student-text hover:text-student-ink ml-auto"
          aria-expanded={showBands}
        >
          Your realistic shot
          <ChevronDown size={13} className={`transition-transform ${showBands ? 'rotate-180' : ''}`} />
        </button>
      </div>

      {showBands && (
        <div className="px-4 pb-3 pt-1 border-t border-divider">
          <ProbabilityBands
            bands={match.probability_bands ?? null}
            reason={bandsReason}
            hideHeading
            className="pt-2"
          />
        </div>
      )}

      {/* ── Actions ── */}
      <div className="flex items-stretch border-t border-divider mt-auto">
        <button
          onClick={onCompare}
          className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 text-[11px] font-medium transition-colors border-r border-divider ${
            comparing ? 'text-cobalt bg-cobalt/10' : 'text-slate hover:bg-muted hover:text-charcoal'
          }`}
          title={comparing ? 'In compare tray' : 'Add to compare'}
        >
          <ArrowRightLeft size={12} />
          <span className="hidden sm:inline">{comparing ? 'In compare' : 'Compare'}</span>
        </button>
        <button
          onClick={onView}
          className="flex-[1.5] flex items-center justify-center gap-1.5 py-2.5 text-[11px] font-semibold text-white bg-cobalt hover:bg-cobalt-dark transition-colors group/view"
        >
          View program
          <ArrowRight size={12} className="group-hover/view:translate-x-0.5 transition-transform" />
        </button>
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
