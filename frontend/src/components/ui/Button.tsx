import { forwardRef } from 'react'
import clsx from 'clsx'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', loading, className, children, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={clsx(
          'inline-flex items-center justify-center rounded-lg font-medium transition-all duration-200 ease-out disabled:opacity-50 disabled:cursor-not-allowed',
          {
            // Primary = Sunlit Gold #FFD60A with soft-ink text + gold glow on hover.
            // Brand spec: --primary / --on-primary / --shadow-glow.
            'bg-gold text-charcoal hover:bg-gold-hover hover:shadow-[0_0_24px_rgba(255,214,10,0.45)]': variant === 'primary',
            // Secondary = Cobalt outline on Paper.
            'border border-cobalt bg-white text-cobalt hover:bg-cobalt hover:text-paper': variant === 'secondary',
            // Ghost = unframed cobalt link, warm-muted bg on hover.
            'text-cobalt hover:bg-student-mist': variant === 'ghost',
            // Danger = editorial brick (#B5321F), not bright rose.
            'bg-[#B5321F] text-paper hover:bg-[#9C2A1A]': variant === 'danger',
            'px-2.5 py-1 text-xs': size === 'sm',
            'px-3.5 py-2 text-sm': size === 'md',
            'px-5 py-2.5 text-base': size === 'lg',
          },
          className
        )}
        {...props}
      >
        {loading && (
          <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        )}
        {children}
      </button>
    )
  }
)

Button.displayName = 'Button'
export default Button
