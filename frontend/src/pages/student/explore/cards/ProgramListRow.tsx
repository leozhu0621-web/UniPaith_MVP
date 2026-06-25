import { Link } from 'react-router-dom'
import {
  Bookmark, BookmarkCheck, BellPlus, BellRing, ChevronRight,
  Calendar, DollarSign, Percent, Building, ArrowRightLeft, Sparkles,
} from 'lucide-react'
import { formatCurrency } from '../../../../utils/format'
import type { ProgramSummary } from '../../../../types'
import { degreeAbbrev, deadlineInfo } from './programFormat'
import { cardLinkClick, CARD_LINK_OVERLAY } from '../shared/cardLink'
import AppStatusPill, { type AppStatus } from './AppStatusPill'

interface Props {
  program: ProgramSummary
  saved: boolean
  onSave: () => void
  onView: () => void
  comparing?: boolean
  onCompare?: () => void
  onAskCounselor?: () => void
  following?: boolean
  onToggleFollow?: () => void
  /** Discover review 2026-06-19 — real application stage for this program, if any. */
  appStatus?: AppStatus | null
  viewHref?: string
}

// Dense list-row variant of ProgramCard (browse grid/list toggle) — one line per
// program for fast scanning. Same stretched-link pattern as the card: the name
// <Link> overlays the row; Save / Follow stay raised sibling buttons.
export default function ProgramListRow({ program, saved, onSave, onView, comparing, onCompare, onAskCounselor, following, onToggleFollow, appStatus, viewHref }: Props) {
  const href = viewHref ?? `/s/programs/${program.id}`
  const abbrev = degreeAbbrev(program.degree_type, program.program_name)
  const deadline = deadlineInfo(program.application_deadline)
  const acceptPct = program.acceptance_rate != null ? Math.round(program.acceptance_rate * 100) : null
  const tuition =
    program.tuition != null ? (program.tuition === 0 ? 'Funded' : formatCurrency(program.tuition)) : null

  return (
    <div className="relative group/row flex items-center gap-3 bg-card border border-border rounded-lg px-4 py-3 elev-subtle hover-lift hover:elev-raised">
      {/* Degree monogram — visual anchor, mirrors the card's tile. */}
      <div className="flex-shrink-0 w-9 h-9 rounded-md bg-muted border border-border/60 flex items-center justify-center">
        <span className="text-[10px] font-bold tracking-wide text-secondary leading-none">{abbrev}</span>
      </div>

      <div className="min-w-0 flex-1">
        <h3 className="text-sm font-semibold text-foreground truncate">
          <Link to={href} onClick={cardLinkClick(onView)} className={CARD_LINK_OVERLAY}>
            {program.program_name}
          </Link>
        </h3>
        <div className="flex items-center gap-1.5 mt-0.5 text-xs text-muted-foreground">
          <AppStatusPill status={appStatus} />
          <Building size={11} className="flex-shrink-0 text-muted-foreground/70" />
          <span className="truncate">
            {program.institution_name}
            {program.institution_city && <span className="text-muted-foreground/70"> · {program.institution_city}</span>}
          </span>
        </div>
      </div>

      {/* Compact stat cluster — display-only, hidden on narrow screens. */}
      <div className="hidden sm:flex items-center gap-3 text-xs text-muted-foreground flex-shrink-0">
        {deadline && !deadline.closed && (
          <span className={`inline-flex items-center gap-1 ${deadline.urgent ? 'text-warning font-semibold' : ''}`} title="Application deadline">
            <Calendar size={12} className={deadline.urgent ? 'text-warning' : 'text-muted-foreground'} />
            {deadline.text}
          </span>
        )}
        {tuition && (
          <span className="inline-flex items-center gap-1" title="Tuition / yr">
            <DollarSign size={12} />
            {tuition}
          </span>
        )}
        {acceptPct != null && (
          <span className="inline-flex items-center gap-1" title="Acceptance rate">
            <Percent size={12} />
            {acceptPct}%
          </span>
        )}
      </div>

      <button
        onClick={e => { e.preventDefault(); e.stopPropagation(); onSave() }}
        aria-label={saved ? 'Remove from list' : 'Save to my list'}
        className={`relative z-10 inline-flex items-center justify-center p-1.5 rounded-md transition-colors flex-shrink-0 ${
          saved ? 'text-secondary' : 'text-muted-foreground hover:bg-muted hover:text-foreground'
        }`}
      >
        {saved ? <BookmarkCheck size={15} /> : <Bookmark size={15} />}
      </button>

      {onCompare && (
        <button
          onClick={e => { e.preventDefault(); e.stopPropagation(); onCompare() }}
          aria-pressed={!!comparing}
          aria-label={comparing ? 'Remove from compare' : 'Add to compare'}
          title={comparing ? 'Comparing' : 'Compare'}
          className={`relative z-10 hidden sm:inline-flex items-center justify-center p-1.5 rounded-md transition-colors flex-shrink-0 ${
            comparing ? 'text-secondary' : 'text-muted-foreground hover:bg-muted hover:text-foreground'
          }`}
        >
          <ArrowRightLeft size={15} />
        </button>
      )}

      {onAskCounselor && (
        <button
          onClick={e => { e.preventDefault(); e.stopPropagation(); onAskCounselor() }}
          aria-label={`Ask about ${program.program_name}`}
          title="Ask about this program"
          className="relative z-10 hidden sm:inline-flex items-center justify-center p-1.5 rounded-md text-muted-foreground hover:bg-muted hover:text-foreground transition-colors flex-shrink-0"
        >
          <Sparkles size={15} />
        </button>
      )}

      {onToggleFollow && (
        <button
          onClick={e => { e.preventDefault(); e.stopPropagation(); onToggleFollow() }}
          aria-pressed={!!following}
          aria-label={following ? `Following ${program.institution_name}` : `Follow ${program.institution_name}`}
          title={following ? `Following ${program.institution_name}` : `Follow ${program.institution_name}`}
          className={`relative z-10 inline-flex items-center justify-center p-1.5 rounded-md transition-colors flex-shrink-0 ${
            following ? 'text-secondary' : 'text-muted-foreground hover:bg-muted hover:text-foreground'
          }`}
        >
          {following ? <BellRing size={15} /> : <BellPlus size={15} />}
        </button>
      )}

      <ChevronRight size={16} className="text-secondary flex-shrink-0 group-hover/row:translate-x-0.5 transition-transform" />
    </div>
  )
}
