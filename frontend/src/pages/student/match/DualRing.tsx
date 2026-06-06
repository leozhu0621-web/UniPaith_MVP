/**
 * Phase C — Dual ring (fitness + confidence).
 *
 * Concentric SVG rings: outer = fitness (match strength), inner =
 * confidence (1 - uncertainty, driven by profile completeness + program
 * data sparseness). Spec calls for both first-class — one number
 * collapses both signals and confuses users.
 *
 * The component is opt-in: existing single-ring consumers keep working
 * with `MatchRing`. Phase C wires this into program detail; card-level
 * retrofit follows.
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

// Duotone per Spec/11 §10: fitness ring = sunlit gold (--primary),
// confidence ring = cobalt (--secondary). No status-color rainbow.
const FITNESS_COLOR = (_v: number) => 'stroke-primary'
const CONFIDENCE_COLOR = (_v: number) => 'stroke-secondary'

export default function DualRing({
  fitness,
  confidence,
  size = 84,
  compact = false,
  className,
  onClick,
}: DualRingProps) {
  const fitnessPct = Math.round(fitness * 100)
  const confidencePct = Math.round(confidence * 100)
  const stroke = 5

  // Outer ring: full radius - stroke. Inner ring: radius - stroke - gap.
  const outerR = (size - stroke) / 2
  const innerR = outerR - stroke - 3
  const outerC = 2 * Math.PI * outerR
  const innerC = 2 * Math.PI * innerR
  const outerOffset = outerC * (1 - fitness)
  const innerOffset = innerC * (1 - confidence)

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
      <div
        className="relative"
        style={{ width: size, height: size }}
      >
        <svg width={size} height={size} className="-rotate-90">
          {/* Tracks */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={outerR}
            fill="none"
            stroke="currentColor"
            strokeWidth={stroke}
            className="text-border"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={innerR}
            fill="none"
            stroke="currentColor"
            strokeWidth={stroke}
            className="text-border"
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
            className={FITNESS_COLOR(fitness)}
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
            className={CONFIDENCE_COLOR(confidence)}
            style={{ transition: 'stroke-dashoffset 0.8s ease-out' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center leading-none">
          <span className="text-base font-bold text-foreground">{fitnessPct}</span>
          <span className="text-[9px] uppercase tracking-wide text-muted-foreground mt-0.5">
            fit
          </span>
        </div>
      </div>
      {!compact && (
        <div className="text-xs">
          <div className="text-foreground font-medium">Fitness · {fitnessPct}%</div>
          <div className="text-muted-foreground">
            Confidence · {confidencePct}%
          </div>
        </div>
      )}
    </div>
  )
}
