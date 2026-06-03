import { forwardRef } from 'react'
import clsx from 'clsx'

// Button — Spec/02-design-system.md §2.
// Variants: primary (gold, rare) · secondary (cobalt, most actions) ·
// tertiary (outline) · ghost · destructive · link. `danger` kept as a
// backward-compatible alias of `destructive`.
// Sizes map to fixed heights: sm 32 / md 40 / lg 48px. Label is 700 weight.
// Focus ring is gold (--ring) even on cobalt, per spec.

type Variant = 'primary' | 'secondary' | 'tertiary' | 'ghost' | 'destructive' | 'danger' | 'link'
type Size = 'sm' | 'md' | 'lg'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  loading?: boolean
}

const VARIANT_CLASSES: Record<Variant, string> = {
  // Gold punctuation — the single accent moment. Ink text.
  primary: 'bg-primary text-primary-foreground hover:brightness-95 active:brightness-90',
  // Cobalt workhorse — Save, Submit, Continue, Send.
  secondary: 'bg-secondary text-secondary-foreground hover:brightness-110 active:brightness-95',
  // Outline — Cancel / secondary actions beside a primary.
  tertiary: 'border border-border bg-transparent text-secondary hover:bg-muted',
  // Unframed — toolbar, kebab, inline table actions.
  ghost: 'bg-transparent text-foreground hover:bg-muted',
  // Editorial brick — Delete, Remove, Withdraw.
  destructive: 'bg-destructive text-destructive-foreground hover:brightness-95 active:brightness-90',
  danger: 'bg-destructive text-destructive-foreground hover:brightness-95 active:brightness-90',
  // Inline link inside paragraph copy.
  link: 'bg-transparent text-secondary underline-offset-4 hover:underline',
}

const SIZE_CLASSES: Record<Size, string> = {
  sm: 'h-8 px-3 text-[13px]',
  md: 'h-10 px-4 text-[13px]',
  lg: 'h-12 px-6 text-base',
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'secondary', size = 'md', loading, className, children, disabled, ...props }, ref) => {
    const isLink = variant === 'link'
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        aria-busy={loading || undefined}
        className={clsx(
          'ui-btn inline-flex items-center justify-center gap-2 rounded-lg font-semibold whitespace-nowrap',
          'transition-all duration-200 ease-out select-none',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 focus-visible:ring-offset-background',
          'disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none',
          !isLink && 'active:translate-y-px',
          VARIANT_CLASSES[variant],
          isLink ? 'h-auto px-0 py-0' : SIZE_CLASSES[size],
          className
        )}
        {...props}
      >
        {loading && (
          <svg className="animate-spin h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" aria-hidden="true">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        )}
        <span className={clsx('inline-flex items-center gap-2', loading && 'opacity-60')}>{children}</span>
      </button>
    )
  }
)

Button.displayName = 'Button'
export default Button
