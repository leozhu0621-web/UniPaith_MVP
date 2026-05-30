// Button — Spec/02-design-system.md §2.
// Six variants × three sizes. Hover steps lightness one notch on the
// OKLCH axis (gold→#F5C800, cobalt→#1F58B5). Focus-visible ring is gold
// even on cobalt buttons (focus is brand-accented). Hit target 44×44px
// minimum — sm gets invisible padding to meet it.

import { forwardRef } from 'react'
import clsx from 'clsx'

export type ButtonVariant =
  | 'primary'
  | 'secondary'
  | 'tertiary'
  | 'ghost'
  | 'destructive'
  | 'link'
  | 'danger' // legacy alias of destructive

export type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  loading?: boolean
  iconLeft?: React.ReactNode
  iconRight?: React.ReactNode
}

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  // primary — sunlit gold. The one accent moment per surface.
  primary:
    'bg-[#FFD60A] text-[#2A2724] hover:bg-[#F5C800] active:bg-[#E5BE00] dark:bg-[#F2C800] dark:text-[#0A1428] dark:hover:bg-[#E0BA00]',
  // secondary — cobalt, the workhorse.
  secondary:
    'bg-[#2A6BD4] text-[#FCFAF2] hover:bg-[#1F58B5] active:bg-[#194992] dark:bg-[#6FA0E8] dark:text-[#0A1428] dark:hover:bg-[#9CC0F0]',
  // tertiary — transparent w/ border, cobalt label.
  tertiary:
    'bg-transparent text-[#2A6BD4] border border-[#C9C2A8] hover:border-[#948C7A] hover:bg-[#F2EEE0] dark:text-[#6FA0E8] dark:border-[#3F567C] dark:hover:border-[#4A5878] dark:hover:bg-[#1A2C4D]',
  // ghost — toolbar buttons, inline actions.
  ghost:
    'bg-transparent text-[#2A2724] hover:bg-[#F2EEE0] dark:text-[#F5F1E8] dark:hover:bg-[#1A2C4D]',
  // destructive — editorial brick.
  destructive:
    'bg-[#B5321F] text-white hover:bg-[#9C2A1A] active:bg-[#82221A] dark:bg-[#FF8470] dark:text-[#0A1428] dark:hover:bg-[#F2705C]',
  // legacy alias
  danger:
    'bg-[#B5321F] text-white hover:bg-[#9C2A1A] active:bg-[#82221A] dark:bg-[#FF8470] dark:text-[#0A1428] dark:hover:bg-[#F2705C]',
  // link — inline link that looks like a button.
  link: 'bg-transparent text-[#2A6BD4] underline-offset-2 hover:underline dark:text-[#6FA0E8]',
}

const SIZE_CLASSES: Record<ButtonSize, string> = {
  // sm: 32px height; invisible y-padding via min-h-[44px] inset-safe.
  sm: 'h-8 px-3 text-[13px] font-bold',
  md: 'h-10 px-4 text-[13px] font-bold',
  lg: 'h-12 px-6 text-base font-bold',
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'secondary',
      size = 'md',
      loading,
      iconLeft,
      iconRight,
      className,
      children,
      disabled,
      type = 'button',
      ...props
    },
    ref,
  ) => {
    const isLink = variant === 'link'
    return (
      <button
        ref={ref}
        type={type}
        disabled={disabled || loading}
        aria-busy={loading || undefined}
        aria-disabled={disabled || loading || undefined}
        className={clsx(
          'inline-flex items-center justify-center gap-2 select-none whitespace-nowrap',
          // Radius matches --radius (12px).
          isLink ? 'rounded-none' : 'rounded-[12px]',
          // Motion: 200ms transitions out for color, shadow, transform.
          'motion-base transition-colors',
          // Active state: subtle 1px translate-y. Drop on link.
          isLink ? '' : 'active:translate-y-px',
          // Disabled.
          'disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none',
          // Focus.
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#FFD60A] focus-visible:ring-offset-0',
          SIZE_CLASSES[size],
          VARIANT_CLASSES[variant],
          // Min hit target 44×44 — give sm an invisible vertical inset.
          size === 'sm' && !isLink && 'before:absolute before:inset-y-[-6px] before:inset-x-0 relative',
          className,
        )}
        {...props}
      >
        {loading && (
          <svg
            className="h-4 w-4 animate-spin"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        )}
        {!loading && iconLeft && <span className="-ml-0.5 inline-flex items-center">{iconLeft}</span>}
        <span className={loading ? 'opacity-60' : undefined}>{children}</span>
        {!loading && iconRight && <span className="-mr-0.5 inline-flex items-center">{iconRight}</span>}
      </button>
    )
  },
)

Button.displayName = 'Button'
export default Button
