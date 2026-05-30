// Badge — Spec/02-design-system.md §9.
// Status badges use soft-bg/solid-text tints; band badges (Reach /
// Target / Safer) get distinct visual treatments so students recognize
// them instantly across surfaces.

import clsx from 'clsx'

export type BadgeVariant =
  | 'neutral'
  | 'success'
  | 'warning'
  | 'danger' // alias of error
  | 'error'
  | 'info'

export type BadgeSize = 'sm' | 'md'

interface BadgeProps {
  variant?: BadgeVariant
  size?: BadgeSize
  children: React.ReactNode
  className?: string
}

const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  // Soft-colored pills, no border.
  // Solid color is the text, soft tint is the bg.
  success:
    'bg-[#DCE8DA] text-[#1F6B2E] dark:bg-[#1E3A2A] dark:text-[#6FCB95]',
  warning:
    'bg-[#F5E6CC] text-[#B8741D] dark:bg-[#3D2E18] dark:text-[#F0B964]',
  error:
    'bg-[#F2D7D0] text-[#B5321F] dark:bg-[#3D1E1A] dark:text-[#FF8470]',
  danger:
    'bg-[#F2D7D0] text-[#B5321F] dark:bg-[#3D1E1A] dark:text-[#FF8470]',
  // info uses secondary (cobalt) soft tint.
  info:
    'bg-[#D9E4F5] text-[#1F58B5] dark:bg-[#1A2C4D] dark:text-[#9CC0F0]',
  neutral:
    'bg-[#F2EEE0] text-[#4A4640] dark:bg-[#1A2C4D] dark:text-[#D9DEE8]',
}

export default function Badge({
  variant = 'neutral',
  size = 'sm',
  children,
  className,
}: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full font-bold whitespace-nowrap',
        VARIANT_CLASSES[variant],
        size === 'sm' ? 'px-2 py-0.5 text-[11px] tracking-wide' : 'px-2.5 py-1 text-[13px]',
        className,
      )}
    >
      {children}
    </span>
  )
}

/* ----------------------------------------------------------------
   BandBadge — Reach / Target / Safer (Spec §9).
   Distinct visual treatments so students recognize them across surfaces.
   ---------------------------------------------------------------- */
export type Band = 'reach' | 'target' | 'safer'

const BAND_CLASSES: Record<Band, string> = {
  reach:
    'border border-[#2A6BD4] text-[#2A6BD4] bg-card dark:border-[#6FA0E8] dark:text-[#6FA0E8]',
  target:
    'bg-[#DCE8DA] text-[#1F6B2E] dark:bg-[#1E3A2A] dark:text-[#6FCB95]',
  safer:
    'bg-[#F2EEE0] text-[#4A4640] dark:bg-[#1A2C4D] dark:text-[#D9DEE8]',
}

const BAND_LABELS: Record<Band, string> = {
  reach: 'Reach',
  target: 'Target',
  safer: 'Safer',
}

export function BandBadge({ band, className }: { band: Band; className?: string }) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-bold tracking-wide',
        BAND_CLASSES[band],
        className,
      )}
      aria-label={`${BAND_LABELS[band]} match`}
    >
      {BAND_LABELS[band]}
    </span>
  )
}

/* ----------------------------------------------------------------
   ConfidenceDots — five filled/empty dots + Low/Medium/High label.
   Used in AI Rationale Popover and score displays (Spec §9, §15).
   ---------------------------------------------------------------- */
type ConfidenceDotsProps = {
  /** 0–5 inclusive. */
  filled: number
  /** Show inline label after dots. */
  showLabel?: boolean
  className?: string
}

export function ConfidenceDots({ filled, showLabel = true, className }: ConfidenceDotsProps) {
  const clamped = Math.max(0, Math.min(5, Math.round(filled)))
  const label = clamped <= 2 ? 'Low' : clamped === 3 ? 'Medium' : 'High'
  return (
    <span
      className={clsx('inline-flex items-center gap-1.5', className)}
      aria-label={`Confidence: ${label} (${clamped} of 5)`}
    >
      <span className="inline-flex items-center gap-1" aria-hidden="true">
        {[0, 1, 2, 3, 4].map(i => (
          <span
            key={i}
            className={clsx(
              'h-2 w-2 rounded-full',
              i < clamped
                ? 'bg-[#FFD60A] dark:bg-[#F2C800]'
                : 'bg-border',
            )}
          />
        ))}
      </span>
      {showLabel && (
        <span className="text-[12px] font-bold text-muted-foreground tracking-wide uppercase">{label}</span>
      )}
    </span>
  )
}

/* ----------------------------------------------------------------
   ConstraintChip — Discovery editable chip (Spec §9).
   Pill, 1px accent border, label format `Category · Value`, trailing ✕
   removes the chip; clicking the label opens an editor in-place.
   ---------------------------------------------------------------- */
type ConstraintChipProps = {
  category: string
  value: string
  onEdit?: () => void
  onRemove?: () => void
  className?: string
}

export function ConstraintChip({
  category,
  value,
  onEdit,
  onRemove,
  className,
}: ConstraintChipProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-stretch rounded-full border border-[#2A6BD4] bg-card text-[13px] motion-base transition-colors',
        'dark:border-[#6FA0E8]',
        className,
      )}
    >
      <button
        type="button"
        onClick={onEdit}
        disabled={!onEdit}
        className={clsx(
          'flex items-center gap-1 pl-3 pr-2 py-1 rounded-l-full',
          onEdit
            ? 'hover:bg-[#F2EEE0] dark:hover:bg-[#1A2C4D] cursor-pointer'
            : 'cursor-default',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#FFD60A]',
        )}
      >
        <span className="text-muted-foreground">{category}</span>
        <span aria-hidden className="text-muted-foreground">·</span>
        <span className="font-bold text-foreground">{value}</span>
      </button>
      {onRemove && (
        <button
          type="button"
          onClick={onRemove}
          aria-label={`Remove constraint: ${category} ${value}`}
          className="px-2 py-1 rounded-r-full border-l border-[#2A6BD4]/40 hover:bg-[#F2EEE0] dark:hover:bg-[#1A2C4D] dark:border-[#6FA0E8]/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#FFD60A]"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M18 6 6 18M6 6l12 12" />
          </svg>
        </button>
      )}
    </span>
  )
}

/* ----------------------------------------------------------------
   AIAssistBadge — visible attribution that AI surfaced something
   (Spec §15.1). Cobalt outline + surface bg; never hide that AI
   produced it.
   ---------------------------------------------------------------- */
export function AIAssistBadge({
  label = 'AI assist',
  className,
}: {
  label?: 'AI assist' | 'AI suggestion'
  className?: string
}) {
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 rounded-full border border-[#2A6BD4] bg-card px-2 py-0.5 text-[11px] font-bold uppercase tracking-wide text-[#2A6BD4]',
        'dark:border-[#6FA0E8] dark:text-[#6FA0E8]',
        className,
      )}
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="10"
        height="10"
        viewBox="0 0 24 24"
        fill="currentColor"
        aria-hidden="true"
      >
        <path d="M12 2 14 9l7 2-7 2-2 7-2-7-7-2 7-2z" />
      </svg>
      {label}
    </span>
  )
}
