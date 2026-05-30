import { forwardRef } from 'react'
import clsx from 'clsx'

// Input — Spec/02-design-system.md §4.
// Label above (never placeholder-as-label). Focus = gold ring + cobalt border.
// error/success states; helper region always reserved so errors don't shift layout.

type FieldSize = 'sm' | 'md' | 'lg'

interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  label?: string
  error?: string
  success?: string
  helperText?: string
  uiSize?: FieldSize
  leftIcon?: React.ReactNode
  required?: boolean
}

const SIZE_CLASSES: Record<FieldSize, string> = {
  sm: 'h-8 text-[13px]',
  md: 'h-10 text-sm',
  lg: 'h-12 text-base',
}

export const fieldBaseClasses =
  'w-full rounded-md border bg-card text-foreground placeholder:text-slate/50 ' +
  'transition-colors focus:outline-none focus-visible:outline-none ' +
  'focus:ring-2 focus:ring-ring focus:border-secondary ' +
  'disabled:bg-muted disabled:text-muted-foreground disabled:cursor-not-allowed'

export function fieldStateClasses(error?: string, success?: string) {
  if (error) return 'border-error bg-error-soft/40 focus:border-error'
  if (success) return 'border-success focus:border-success'
  return 'border-border hover:border-charcoal/30'
}

export function FieldLabel({ htmlFor, children, required }: { htmlFor?: string; children: React.ReactNode; required?: boolean }) {
  return (
    <label htmlFor={htmlFor} className="block text-[13px] font-semibold text-muted-foreground mb-1.5">
      {children}
      {required && <span className="text-error ml-0.5" aria-hidden="true">*</span>}
    </label>
  )
}

export function FieldHelp({ error, success, helperText }: { error?: string; success?: string; helperText?: string }) {
  return (
    <div className="min-h-[18px] mt-1">
      {error ? (
        <p className="text-xs text-error">{error}</p>
      ) : success ? (
        <p className="text-xs text-success">{success}</p>
      ) : helperText ? (
        <p className="text-xs text-muted-foreground">{helperText}</p>
      ) : null}
    </div>
  )
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, success, helperText, uiSize = 'md', leftIcon, className, id, required, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-')
    const helperId = inputId ? `${inputId}-help` : undefined
    return (
      <div className="w-full">
        {label && <FieldLabel htmlFor={inputId} required={required}>{label}</FieldLabel>}
        <div className="relative">
          {leftIcon && (
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none">
              {leftIcon}
            </span>
          )}
          <input
            ref={ref}
            id={inputId}
            aria-invalid={error ? true : undefined}
            aria-describedby={helperId}
            aria-required={required || undefined}
            className={clsx(
              fieldBaseClasses,
              fieldStateClasses(error, success),
              SIZE_CLASSES[uiSize],
              leftIcon ? 'pl-9 pr-3' : 'px-3',
              className
            )}
            {...props}
          />
        </div>
        <div id={helperId}>
          <FieldHelp error={error} success={success} helperText={helperText} />
        </div>
      </div>
    )
  }
)

Input.displayName = 'Input'
export default Input
