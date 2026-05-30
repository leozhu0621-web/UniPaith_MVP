// AIRationalePopover — Spec/02-design-system.md §6 (named pattern).
// "Why this match" popover used by every AI surface in the app. Three
// regions: heading + plain-language reason + confidence meter + signal
// chips. Signal chips are clickable to open a deeper drill-down.

import Popover from './Popover'
import { ConfidenceDots, AIAssistBadge } from './Badge'
import clsx from 'clsx'

export type RationaleSignal = {
  /** Short, human-readable signal name. */
  label: string
  /** Optional drill-down handler. */
  onClick?: () => void
}

interface AIRationalePopoverProps {
  title?: string
  /** Plain-language reason text. Sentence-case. */
  reason: string
  /** 0–5 inclusive. Derived from the confidence score. */
  confidenceFilled: number
  /** Signal chips — what the AI based its conclusion on. */
  signals?: RationaleSignal[]
  /** Optional ISO timestamp of the last AI run (Spec §15.3). */
  lastRunAt?: string
  /** Render-prop trigger that toggles the popover. */
  trigger: (props: { toggle: () => void; open: boolean }) => React.ReactNode
  placement?: 'bottom-start' | 'bottom-end' | 'top-start' | 'top-end'
}

function formatTimestamp(iso?: string) {
  if (!iso) return null
  try {
    const d = new Date(iso)
    return d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
  } catch {
    return null
  }
}

export default function AIRationalePopover({
  title = 'Why this match',
  reason,
  confidenceFilled,
  signals = [],
  lastRunAt,
  trigger,
  placement = 'bottom-end',
}: AIRationalePopoverProps) {
  const stamp = formatTimestamp(lastRunAt)
  return (
    <Popover trigger={trigger} placement={placement} className="w-[320px] max-w-[calc(100vw-2rem)]">
      {({ close }) => (
        <div className="space-y-3">
          <div className="flex items-start justify-between gap-2">
            <h3 className="text-[15px] font-bold leading-[1.3]">{title}</h3>
            <AIAssistBadge />
          </div>

          <p className="text-base text-foreground/85 leading-[1.55]">{reason}</p>

          <div className="border-t border-border pt-3 flex items-center justify-between gap-2">
            <span className="up-eyebrow text-muted-foreground" style={{ color: 'inherit' }}>
              Confidence
            </span>
            <ConfidenceDots filled={confidenceFilled} />
          </div>

          {signals.length > 0 && (
            <div className="border-t border-border pt-3">
              <div className="up-eyebrow text-muted-foreground mb-2" style={{ color: 'inherit' }}>
                Based on
              </div>
              <ul className="flex flex-wrap gap-1.5">
                {signals.map(sig => (
                  <li key={sig.label}>
                    <button
                      type="button"
                      onClick={() => {
                        sig.onClick?.()
                        if (sig.onClick) close()
                      }}
                      className={clsx(
                        'inline-flex items-center rounded-full border border-[#2A6BD4] bg-card px-2.5 py-0.5 text-[12px] motion-base transition-colors',
                        'dark:border-[#6FA0E8]',
                        sig.onClick
                          ? 'hover:bg-[#F2EEE0] dark:hover:bg-[#1A2C4D] cursor-pointer'
                          : 'cursor-default',
                        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#FFD60A]',
                      )}
                      tabIndex={sig.onClick ? 0 : -1}
                    >
                      {sig.label}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {stamp && (
            <p className="text-[12px] text-muted-foreground border-t border-border pt-3">
              Last updated · {stamp}
            </p>
          )}
        </div>
      )}
    </Popover>
  )
}
