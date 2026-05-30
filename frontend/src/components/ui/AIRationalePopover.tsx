import { Sparkles, RefreshCw } from 'lucide-react'
import clsx from 'clsx'
import Popover from './Popover'
import ConfidenceDots from './ConfidenceDots'

// AI surfaces — Spec/02-design-system.md §6 (AI Rationale Popover anatomy) + §15.
// Every score/ranking/recommendation gets a "Why" affordance that opens this.

export function AIBadge({ label = 'AI assist', className }: { label?: string; className?: string }) {
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 rounded-pill border border-accent bg-card px-2 py-0.5 text-[11px] font-semibold text-accent',
        className
      )}
    >
      <Sparkles size={11} />
      {label}
    </span>
  )
}

export interface RationaleContentProps {
  title?: string
  reason?: string
  loading?: boolean
  /** 0–100 confidence; renders the 5-dot meter. */
  confidence?: number
  signals?: string[]
  onSignalClick?: (signal: string) => void
  /** When the LLM agent failed and we fell back to the rule-based path. */
  isFallback?: boolean
  onRefresh?: () => void
  lastRunAt?: string
}

export function RationaleContent({
  title = 'Why this match',
  reason,
  loading,
  confidence,
  signals,
  onSignalClick,
  isFallback,
  onRefresh,
  lastRunAt,
}: RationaleContentProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-2">
        <h3 className="flex items-center gap-1.5 text-sm font-semibold text-foreground">
          <Sparkles size={14} className="text-primary" />
          {title}
        </h3>
        {onRefresh && (
          <button
            onClick={onRefresh}
            aria-label="Regenerate"
            className="p-1 rounded text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : undefined} />
          </button>
        )}
      </div>

      {loading && !reason ? (
        <p className="text-sm text-muted-foreground">Analyzing…</p>
      ) : (
        reason && <p className="text-sm leading-relaxed text-foreground whitespace-pre-line">{reason}</p>
      )}

      {typeof confidence === 'number' && (
        <div className="flex items-center gap-2 border-t border-border pt-3">
          <span className="text-xs font-semibold text-muted-foreground">Confidence</span>
          <ConfidenceDots value={confidence} />
        </div>
      )}

      {signals && signals.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-eyebrow text-muted-foreground">Based on</p>
          <div className="flex flex-wrap gap-1.5">
            {signals.map(s => (
              <button
                key={s}
                type="button"
                onClick={onSignalClick ? () => onSignalClick(s) : undefined}
                disabled={!onSignalClick}
                className={clsx(
                  'rounded-pill border border-cobalt px-2 py-0.5 text-xs text-cobalt',
                  onSignalClick && 'hover:bg-cobalt/10 transition-colors'
                )}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {isFallback && (
        <p className="text-xs text-muted-foreground italic">Showing rule-based result.</p>
      )}
      {lastRunAt && (
        <p className="text-[11px] text-muted-foreground">Updated {lastRunAt}</p>
      )}
    </div>
  )
}

interface AIRationalePopoverProps extends RationaleContentProps {
  trigger?: React.ReactNode
  align?: 'start' | 'center' | 'end'
}

export default function AIRationalePopover({ trigger, align = 'start', ...content }: AIRationalePopoverProps) {
  return (
    <Popover
      align={align}
      trigger={
        trigger ?? (
          <span className="inline-flex items-center gap-1 text-xs font-semibold text-secondary hover:underline">
            <Sparkles size={12} /> Why
          </span>
        )
      }
    >
      <RationaleContent {...content} />
    </Popover>
  )
}
