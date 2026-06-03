import clsx from 'clsx'

// Status badge — Spec/02-design-system.md §9. Pill, no border, soft-colored.
type BadgeVariant = 'success' | 'warning' | 'danger' | 'error' | 'info' | 'neutral'

interface BadgeProps {
  variant?: BadgeVariant
  size?: 'sm' | 'md'
  children: React.ReactNode
  className?: string
}

const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  success: 'bg-success-soft text-success',
  warning: 'bg-warning-soft text-warning',
  danger: 'bg-error-soft text-error',
  error: 'bg-error-soft text-error',
  info: 'bg-secondary/10 text-secondary',
  neutral: 'bg-muted text-muted-foreground',
}

export default function Badge({ variant = 'neutral', size = 'sm', children, className }: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 rounded-pill font-semibold',
        VARIANT_CLASSES[variant],
        size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-sm',
        className
      )}
    >
      {children}
    </span>
  )
}
