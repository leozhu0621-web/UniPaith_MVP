import clsx from 'clsx'
import { Check, type LucideIcon } from 'lucide-react'

/**
 * Imprint-style big tappable option card (UX overhaul Ship C §3): icon +
 * label (+ hint), cobalt ring + check when selected, springy press/select
 * scale via --ease-spring. Native <button> → Tab/Enter/Space for free.
 */
interface OptionCardProps {
  label: string
  icon?: LucideIcon
  hint?: string
  selected: boolean
  onSelect: () => void
  /** Multi-select renders a checkbox affordance instead of radio semantics. */
  multi?: boolean
  /** Compact chip-card (interest grid) vs full-height card. */
  size?: 'lg' | 'chip'
}

export default function OptionCard({
  label,
  icon: Icon,
  hint,
  selected,
  onSelect,
  multi = false,
  size = 'lg',
}: OptionCardProps) {
  return (
    <button
      type="button"
      role={multi ? 'checkbox' : 'radio'}
      aria-checked={selected}
      onClick={onSelect}
      style={{ transitionTimingFunction: 'var(--ease-spring)' }}
      className={clsx(
        'group relative w-full text-left rounded-xl border-2 bg-card transition-all duration-200',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background',
        'active:scale-[0.97]',
        size === 'lg' ? 'p-4 sm:p-5' : 'px-3 py-2.5',
        selected
          ? 'border-secondary bg-secondary/5 scale-[1.02] elev-raised'
          : 'border-border hover:border-secondary/40 hover:bg-muted/50'
      )}
    >
      <span className={clsx('flex items-center', size === 'lg' ? 'gap-4' : 'gap-2.5')}>
        {Icon && (
          <span
            className={clsx(
              'flex shrink-0 items-center justify-center rounded-lg transition-colors',
              size === 'lg' ? 'h-11 w-11' : 'h-8 w-8',
              selected ? 'bg-secondary text-secondary-foreground' : 'bg-secondary/10 text-secondary'
            )}
          >
            <Icon size={size === 'lg' ? 22 : 16} />
          </span>
        )}
        <span className="min-w-0 flex-1">
          <span
            className={clsx(
              'block font-semibold text-foreground break-words',
              size === 'lg' ? 'text-base' : 'text-[13px] leading-snug'
            )}
          >
            {label}
          </span>
          {hint && size === 'lg' && (
            <span className="mt-0.5 block text-sm text-muted-foreground">{hint}</span>
          )}
        </span>
        <span
          aria-hidden
          className={clsx(
            'flex shrink-0 items-center justify-center rounded-full transition-all duration-200',
            size === 'lg' ? 'h-6 w-6' : 'h-5 w-5',
            selected
              ? 'bg-secondary text-secondary-foreground scale-100'
              : 'border border-border bg-transparent text-transparent scale-90'
          )}
          style={{ transitionTimingFunction: 'var(--ease-spring)' }}
        >
          <Check size={size === 'lg' ? 14 : 12} strokeWidth={3} />
        </span>
      </span>
    </button>
  )
}
