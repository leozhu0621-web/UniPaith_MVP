/**
 * Dual ring (fitness + confidence) — brand-aligned.
 *
 * Outer ring = fitness (match strength); inner ring = confidence
 * (1 - uncertainty from profile completeness + program data sparseness).
 * Spec calls for both first-class — one number collapses both signals
 * and confuses users. Colors use the canonical status palette so
 * fitness reads correctly across light + dark themes.
 */
import clsx from 'clsx'

export interface DualRingProps {
  /** 0..1. Match strength against the active strategy. */
  fitness: number
  /** 0..1. How sure we are about the fitness number. */
  confidence: number
  size?: number
  /** Compact = numbers only, no labels. */
  compact?: boolean
  className?: string
  onClick?: () => void
}

// Brand status palette — success/cobalt/warning/error tones.
const FITNESS_STROKE = (v: number) => {
  if (v >= 0.85) return 'stroke-success'
  if (v >= 0.7) return 'stroke-cobalt'
  if (v >= 0.5) return 'stroke-warning'
  return 'stroke-error'
}

// Inner ring stays neutral so it reads as a qualifier, not competing data.
const CONFIDENCE_STROKE = (v: number) => {
  if (v >= 0.7) return 'stroke-charcoal'
  if (v >= 0.4) return 'stroke-slate'
  return 'stroke-stone'
}

export default function DualRing({
  fitness,
  confidence,
  size = 84,
  compact = false,
  className,
  onClick,
}: DualRingProps) {
  const fitnessPct = Math.round(clamp01(fitness) * 100)
  const confidencePct = Math.round(clamp01(confidence) * 100)
  const stroke = 5

  const outerR = (size - stroke) / 2
  const innerR = outerR - stroke - 3
  const outerC = 2 * Math.PI * outerR
  const innerC = 2 * Math.PI * innerR
  const outerOffset = outerC * (1 - clamp01(fitness))
  const innerOffset = innerC * (1 - clamp01(confidence))

  const interactive = !!onClick

  return (
    <div
      className={clsx(
        'inline-flex items-center gap-3',
        interactive && 'cursor-pointer group',
        className,
      )}
      onClick={onClick}
      role={interactive ? 'button' : undefined}
      tabIndex={interactive ? 0 : undefined}
      onKeyDown={
        interactive
          ? e => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                onClick?.()
              }
            }
          : undefined
      }
      aria-label={
        interactive
          ? `Match — fitness ${fitnessPct}%, confidence ${confidencePct}%. Click for explanation.`
          : `Match — fitness ${fitnessPct}%, confidence ${confidencePct}%.`
      }
    >
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          {/* Tracks */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={outerR}
            fill="none"
            stroke="currentColor"
            strokeWidth={stroke}
            className="text-divider"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={innerR}
            fill="none"
            stroke="currentColor"
            strokeWidth={stroke}
            className="text-divider"
          />
          {/* Fitness — outer */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={outerR}
            fill="none"
            stroke="currentColor"
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={outerC}
            strokeDashoffset={outerOffset}
            className={FITNESS_STROKE(fitness)}
            style={{ transition: 'stroke-dashoffset 0.8s ease-out' }}
          />
          {/* Confidence — inner */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={innerR}
            fill="none"
            stroke="currentColor"
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={innerC}
            strokeDashoffset={innerOffset}
            className={CONFIDENCE_STROKE(confidence)}
            style={{ transition: 'stroke-dashoffset 0.8s ease-out' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center leading-none">
          <span className="text-base font-bold text-charcoal">{fitnessPct}</span>
          <span className="text-[9px] uppercase tracking-wider text-slate mt-0.5">
            fit
          </span>
        </div>
      </div>
      {!compact && (
        <div className="text-xs">
          <div className="text-charcoal font-bold">Fitness · {fitnessPct}%</div>
          <div className="text-slate">Confidence · {confidencePct}%</div>
        </div>
      )}
    </div>
  )
}

function clamp01(n: number): number {
  if (!Number.isFinite(n)) return 0
  if (n < 0) return 0
  if (n > 1) return 1
  return n
}
